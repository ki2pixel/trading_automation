"""
Accumulator Pattern – Buffer de rétention des profits USDC.
Accumule les plus-values réalisées et ne déclenche la conversion
vers EUR que lorsque le seuil minimum est atteint.
"""
from decimal import Decimal
from datetime import datetime, timezone
from typing import Tuple
import logging

logger = logging.getLogger("bybit.conversion")

# Seuil minimum strict pour déclencher une conversion (configurable)
DEFAULT_TRIGGER_THRESHOLD = Decimal("15.00")  # USDC
MINIMUM_ALLOWED_THRESHOLD = Decimal("5.00")   # Plancher de sécurité

class AccumulatorBuffer:
    """
    Registre persistant d'accumulation des profits USDC.

    Responsabilités:
    - Enregistrer chaque plus-value réalisée via deposit()
    - Évaluer le franchissement du seuil via should_trigger()
    - Fournir le solde accumulé via get_balance()
    - Marquer le buffer comme drainé après conversion via drain()
    """

    def __init__(
        self,
        threshold: Decimal = DEFAULT_TRIGGER_THRESHOLD,
        source: str = "bybit"
    ):
        if threshold < MINIMUM_ALLOWED_THRESHOLD:
            raise ValueError(
                f"Threshold {threshold} is below minimum allowed "
                f"({MINIMUM_ALLOWED_THRESHOLD} USDC)"
            )
        self.threshold = threshold
        self.source = source

    def deposit(self, conn, amount: Decimal, trade_ref: str = "") -> Decimal:
        """
        Enregistre un profit réalisé dans le buffer.
        Retourne le nouveau solde accumulé.
        Utilise Decimal exclusivement – float interdit.
        """
        if not isinstance(amount, Decimal):
            raise TypeError(f"amount must be Decimal, got {type(amount)}")
        if amount <= Decimal("0"):
            raise ValueError("Cannot deposit non-positive amount")

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversion_accumulator (source, amount, trade_ref, created_at)
                VALUES (%s, %s, %s, %s)
            """, (self.source, amount, trade_ref, datetime.now(timezone.utc)))

            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM conversion_accumulator
                WHERE source = %s AND drained = FALSE
            """, (self.source,))
            balance = Decimal(str(cur.fetchone()[0]))

        conn.commit()
        logger.info(
            f"[Accumulator] Deposited {amount} USDC (ref: {trade_ref}). "
            f"Buffer balance: {balance} USDC"
        )
        return balance

    def get_balance(self, conn) -> Decimal:
        """Retourne le solde non-drainé du buffer."""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM conversion_accumulator
                WHERE source = %s AND drained = FALSE
            """, (self.source,))
            return Decimal(str(cur.fetchone()[0]))

    def should_trigger(self, conn) -> Tuple[bool, Decimal]:
        """
        Évalue si le seuil d'accumulation est atteint.
        Retourne (should_convert, current_balance).
        """
        balance = self.get_balance(conn)
        return balance >= self.threshold, balance

    def drain(self, conn, conversion_id: str) -> Decimal:
        """
        Marque toutes les entrées non-drainées comme drainées.
        Associe l'ID de conversion pour traçabilité.
        Retourne le montant total drainé.
        """
        balance = self.get_balance(conn)
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE conversion_accumulator
                SET drained = TRUE, conversion_id = %s, drained_at = %s
                WHERE source = %s AND drained = FALSE
            """, (conversion_id, datetime.now(timezone.utc), self.source))
        conn.commit()
        logger.info(
            f"[Accumulator] Drained {balance} USDC (conversion: {conversion_id})"
        )
        return balance
