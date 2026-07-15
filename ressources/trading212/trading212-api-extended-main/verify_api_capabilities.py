"""
Script de vérification empirique pour tester les capacités de l'API Trading 212 (Beta).

Ce script permet de :
1. Vérifier si l'endpoint /equity/metadata/instruments renvoie des prix actualisés.
2. Tester l'existence d'endpoints de cotation directs comme /equity/prices ou /equity/quotes.
3. Vérifier le comportement de /equity/positions?ticker=... lorsqu'aucune position n'est détenue.
4. Analyser les en-têtes de limitation de taux (Rate Limiting) pour évaluer la viabilité.

Usage:
    export T212_API_KEY_ID="votre_id"
    export T212_API_SECRET="votre_secret"
    python verify_api_capabilities.py
"""

import argparse
import os
import sys
import time
from typing import Any, Dict, List, Optional
import requests
from requests.auth import HTTPBasicAuth


class Trading212Verifier:
    """Classe de vérification des capacités et limites de l'API Trading 212."""

    def __init__(self, api_key_id: str, api_secret: str, host: str = "https://demo.trading212.com"):
        self.host = host
        self.auth = HTTPBasicAuth(api_key_id, api_secret)
        self.headers = {"Content-Type": "application/json"}
        self._last_request_time = 0.0
        self._min_delay = 2.5  # Respecter le rate limit global de base

    def _throttle(self) -> None:
        """Méthode d'attente pour respecter les limitations de requêtes."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request_time = time.time()

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Effectue une requête HTTP et retourne la réponse brute pour analyse des en-têtes."""
        self._throttle()
        url = f"{self.host}/api/v0{endpoint}"
        response = requests.request(
            method,
            url,
            auth=self.auth,
            headers=self.headers,
            params=params,
            timeout=30
        )
        return response

    def check_instruments_metadata(self) -> None:
        """Vérifie si les métadonnées des instruments contiennent des prix."""
        print("\n--- 1. Audit de /equity/metadata/instruments ---")
        try:
            response = self._request("GET", "/equity/metadata/instruments")
            print(f"Statut HTTP : {response.status_code}")

            # Afficher les en-têtes de limitation de taux
            self.print_rate_limits(response)

            instruments: List[Dict[str, Any]] = response.json()
            print(f"Nombre total d'instruments renvoyés : {len(instruments)}")

            if not instruments:
                print("Aucun instrument disponible.")
                return

            # Analyser le premier instrument pour voir si des champs de prix existent
            first_inst = instruments[0]
            print(f"Structure d'un instrument exemple ({first_inst.get('ticker')}) :")
            for key, val in first_inst.items():
                print(f"  - {key} : {val} ({type(val).__name__})")

            # Vérifier explicitement la présence de mots clés liés aux prix
            price_keys = ["price", "currentPrice", "lastPrice", "ask", "bid", "quote"]
            found_keys = [k for k in price_keys if k in first_inst]
            if found_keys:
                print(f"⚠️ CHAMPS DE PRIX TROUVÉS : {found_keys}")
            else:
                print("✅ Aucun champ de prix/cotation trouvé dans les métadonnées (uniquement des données de structure).")

        except Exception as e:
            print(f"Erreur lors de l'appel : {e}")

    def check_undocumented_price_endpoints(self) -> None:
        """Tente d'appeler des routes de prix hypothétiques pour voir si elles existent."""
        print("\n--- 2. Test d'endpoints de cotation directe (hypothétiques) ---")
        endpoints_to_test = [
            "/equity/prices",
            "/equity/quotes",
            "/equity/ticker",
            "/equity/metadata/prices"
        ]

        # On teste avec un ticker connu (SAP SE sur Xetra)
        params = {"ticker": "SAP_GY_EQ"}

        for endpoint in endpoints_to_test:
            print(f"Appel de {endpoint} ...")
            try:
                response = self._request("GET", endpoint, params=params)
                print(f"  -> Statut HTTP : {response.status_code}")
                if response.status_code == 200:
                    print(f"  🎉 ENDPOINT DÉCOUVERT ! Réponse : {response.text[:200]}")
                elif response.status_code == 404:
                    print("  -> Non trouvé (404). Ce point d'accès n'existe pas.")
                else:
                    print(f"  -> Réponse inattendue ({response.status_code}) : {response.text[:200]}")
            except Exception as e:
                print(f"  -> Erreur : {e}")

    def check_position_without_owning(self, ticker: str = "SAP_GY_EQ") -> None:
        """Vérifie le comportement de l'API positions pour un ticker non détenu."""
        print(f"\n--- 3. Test de /equity/positions?ticker={ticker} ---")
        try:
            # On demande la position spécifique pour le ticker que l'on n'a pas en portefeuille
            response = self._request("GET", f"/equity/positions?ticker={ticker}")
            print(f"Statut HTTP : {response.status_code}")
            self.print_rate_limits(response)

            try:
                data = response.json()
                print(f"Réponse JSON reçue : {data}")
            except ValueError:
                print(f"Réponse brute (non-JSON) : {response.text}")

        except requests.exceptions.HTTPError as e:
            print(f"Erreur HTTP : {e}")
        except Exception as e:
            print(f"Erreur : {e}")

    def print_rate_limits(self, response: requests.Response) -> None:
        """Affiche les en-têtes de Rate Limiting s'ils sont présents dans la réponse."""
        rate_headers = {
            "x-ratelimit-limit": "Limite max de requêtes",
            "x-ratelimit-period": "Période (secondes)",
            "x-ratelimit-remaining": "Requêtes restantes",
            "x-ratelimit-reset": "Temps de reset (secondes)",
            "x-ratelimit-used": "Requêtes consommées"
        }
        limits_found = False
        for header, desc in rate_headers.items():
            val = response.headers.get(header)
            if val is not None:
                print(f"  - {desc} ({header}) : {val}")
                limits_found = True
        if not limits_found:
            print("  - Aucun en-tête de Rate Limiting détecté dans la réponse.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Vérificateur d'API Trading 212")
    parser.add_argument("--api-key-id", default=os.getenv("T212_API_KEY_ID"), help="ID de la clé API")
    parser.add_argument("--api-secret", default=os.getenv("T212_API_SECRET"), help="Clé secrète")
    args = parser.parse_args()

    # Si les variables ne sont pas fournies, on tente de les récupérer avec les variables étendues
    api_key_id = args.api_key_id or os.getenv("T212_API_KEY")
    api_secret = args.api_secret or os.getenv("T212_API_SECRET")

    if not api_key_id or not api_secret:
        print("ERREUR : Clé API et Secret non configurés.")
        print("Veuillez les exporter dans votre environnement :")
        print("  export T212_API_KEY_ID=\"ton_id\"")
        print("  export T212_API_SECRET=\"ta_secret\"")
        sys.exit(1)

    print("==========================================================")
    print("VÉRIFICATION DES CAPACITÉS DE COTATION DIRECTE - TRADING 212")
    print("==========================================================")

    verifier = Trading212Verifier(api_key_id=api_key_id, api_secret=api_secret)

    verifier.check_instruments_metadata()
    verifier.check_undocumented_price_endpoints()
    verifier.check_position_without_owning()


if __name__ == "__main__":
    main()
