"""
UTA Margin Simulator – Pre-trade risk controller.
Interroge l'état du compte UTA et modélise l'impact d'une
soustraction de collatéral AVANT émission de l'ordre de conversion.
"""
from decimal import Decimal
from typing import NamedTuple, Optional
import logging

logger = logging.getLogger("bybit.conversion")

SAFETY_FACTOR = Decimal("1.2")  # Multiplicateur de sécurité sur la MM


class MarginState(NamedTuple):
    """Snapshot de l'état de marge du compte UTA."""
    total_equity: Decimal          # Equity totale du compte
    account_margin_rate: Decimal   # IMR ou MMR actuel (ratio)
    total_maintenance_margin: Decimal  # Marge de maintien totale
    available_balance: Decimal     # Solde disponible pour trading


class MarginCheckResult(NamedTuple):
    """Résultat du pre-trade check de marge."""
    is_safe: bool
    margin_state: MarginState
    post_conversion_equity: Decimal
    required_minimum: Decimal
    headroom: Decimal  # post_equity - required_minimum
    reason: str


class UTAMarginSimulator:
    """
    Contrôleur de risque pré-conversion.
    
    Workflow:
    1. Interroge GET /v5/account/wallet-balance pour obtenir l'état de marge
    2. Modélise: (Equity - amount_to_convert) > (MM × safety_factor)
    3. Retourne un verdict structuré (MarginCheckResult)
    
    Contrainte: Utilise exclusivement Decimal. Float interdit.
    """

    def __init__(self, bybit_client, safety_factor: Decimal = SAFETY_FACTOR):
        self.client = bybit_client
        self.safety_factor = safety_factor
        self._conversion_locked = False
        self._lock_reason: Optional[str] = None

    def fetch_margin_state(self) -> MarginState:
        """
        Interroge l'endpoint /v5/account/wallet-balance via le client
        pour extraire l'état de marge du compte UTA.
        """
        base_coin = self.client.config.base_currency
        data = self.client.get_account_summary(coin=base_coin)
        
        # Naviguer dans la structure de réponse Bybit V5
        result_list = data.get("result", {}).get("list", [])
        if not result_list:
            raise ValueError(f"No account summary returned from Bybit: {data}")
            
        acc_info = result_list[0]
        
        total_equity = Decimal(str(acc_info.get("totalEquity", "0")))
        total_mm = Decimal(str(acc_info.get("totalMaintenanceMargin", "0")))
        available = Decimal(str(acc_info.get("totalAvailableBalance", "0")))
        
        # Calculer le ratio de marge de maintien (MMR)
        if total_equity > Decimal("0"):
            mmr = total_mm / total_equity
        else:
            mmr = Decimal("0")
        
        return MarginState(
            total_equity=total_equity,
            account_margin_rate=mmr,
            total_maintenance_margin=total_mm,
            available_balance=available,
        )

    def check_conversion_safety(
        self, amount_usdc: Decimal
    ) -> MarginCheckResult:
        """
        Pre-trade check : peut-on convertir `amount_usdc` sans
        mettre en danger les positions ouvertes ?
        
        Logique:
        - EUR a un ratio de collatéral de 0% dans l'UTA
        - Convertir X USDC → EUR détruit X de collatéral
        - La conversion est sûre si:
          (Equity - X) > (Maintenance_Margin × safety_factor)
        """
        if not isinstance(amount_usdc, Decimal):
            raise TypeError(f"amount must be Decimal, got {type(amount_usdc)}")
        
        state = self.fetch_margin_state()
        
        post_equity = state.total_equity - amount_usdc
        required_min = state.total_maintenance_margin * self.safety_factor
        headroom = post_equity - required_min
        
        # Cas trivial: pas de positions ouvertes (MM = 0)
        if state.total_maintenance_margin == Decimal("0"):
            return MarginCheckResult(
                is_safe=True,
                margin_state=state,
                post_conversion_equity=post_equity,
                required_minimum=required_min,
                headroom=headroom,
                reason="No open derivative positions – conversion safe"
            )
        
        is_safe = headroom > Decimal("0")
        
        if is_safe:
            reason = (
                f"Safe: post-conversion equity ({post_equity} USD) > "
                f"required minimum ({required_min} USD). "
                f"Headroom: {headroom} USD"
            )
            logger.info(f"[MarginSimulator] {reason}")
        else:
            reason = (
                f"UNSAFE: post-conversion equity ({post_equity} USD) < "
                f"required minimum ({required_min} USD). "
                f"Deficit: {abs(headroom)} USD. CONVERSION BLOCKED."
            )
            logger.warning(f"[MarginSimulator] {reason}")
            self._conversion_locked = True
            self._lock_reason = reason
        
        return MarginCheckResult(
            is_safe=is_safe,
            margin_state=state,
            post_conversion_equity=post_equity,
            required_minimum=required_min,
            headroom=headroom,
            reason=reason
        )

    @property
    def is_locked(self) -> bool:
        return self._conversion_locked

    def unlock(self) -> None:
        """Déverrouillage manuel après résolution de la situation de marge."""
        self._conversion_locked = False
        self._lock_reason = None
        logger.info("[MarginSimulator] Conversion lock released manually")
