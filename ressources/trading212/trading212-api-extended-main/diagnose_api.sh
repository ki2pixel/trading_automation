#!/bin/bash
echo "=== Diagnostic API Trading212 ==="
echo ""
echo "1. Vérification des variables d'environnement:"
echo "   T212_API_KEY_ID: $([ -n "$T212_API_KEY_ID" ] && echo 'Défini' || echo 'NON DÉFINI')"
echo "   T212_API_SECRET: $([ -n "$T212_API_SECRET" ] && echo 'Défini' || echo 'NON DÉFINI')"
echo ""
echo "2. Test DEMO avec Basic Auth:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" \
  -u "$T212_API_KEY_ID:$T212_API_SECRET" \
  https://demo.trading212.com/api/v0/equity/account/summary
echo ""
echo "3. Test LIVE avec Basic Auth:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" \
  -u "$T212_API_KEY_ID:$T212_API_SECRET" \
  https://live.trading212.com/api/v0/equity/account/summary
echo ""
echo "4. Test DEMO avec header Authorization explicite:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" \
  -H "Authorization: Basic $(echo -n "$T212_API_KEY_ID:$T212_API_SECRET" | base64 -w 0)" \
  https://demo.trading212.com/api/v0/equity/account/summary
echo ""
echo "5. Test LIVE avec header Authorization explicite:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" \
  -H "Authorization: Basic $(echo -n "$T212_API_KEY_ID:$T212_API_SECRET" | base64 -w 0)" \
  https://live.trading212.com/api/v0/equity/account/summary
echo ""
