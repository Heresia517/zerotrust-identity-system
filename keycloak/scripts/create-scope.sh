#!/bin/bash
# create-scope.sh – Création du scope OAuth2 'did' dans le realm zt-decentralized-iam

# Charge les variables d'environnement depuis le fichier .env à la racine
source ../../.env

KEYCLOAK_URL="http://localhost:8080"
REALM="zt-decentralized-iam"
ADMIN_USER="admin"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin123}"

# Obtenir le token d'accès admin
ADMIN_TOKEN=$(curl -s -X POST \
  "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=admin-cli" \
  -d "username=${ADMIN_USER}" \
  -d "password=${ADMIN_PASS}" \
  -d "grant_type=password" | jq -r '.access_token')

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
  echo "Erreur : impossible d'obtenir le token."
  exit 1
fi

# Création du scope 'did'
echo "Création du scope 'did'..."
curl -s -X POST \
  "${KEYCLOAK_URL}/admin/realms/${REALM}/client-scopes" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "did",
    "description": "Scope pour inclure le DID Ethereum dans les tokens JWT",
    "protocol": "openid-connect",
    "attributes": {
      "include.in.token.scope": "true",
      "display.on.consent.screen": "true",
      "consent.screen.text": "Accès à votre identifiant décentralisé (DID)"
    }
  }'

echo "Scope 'did' créé avec succès."