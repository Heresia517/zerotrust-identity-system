#!/bin/bash
# create-clients.sh – Création des clients OAuth2 dans le realm zt-decentralized-iam

source ../../.env   # charge les variables d'environnement

KEYCLOAK_URL="http://localhost:8080"
REALM="zt-decentralized-iam"
ADMIN_USER="admin"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin123}"

# Obtenir le token admin
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

# Création du client frontend
echo "Création du client frontend..."
curl -s -X POST \
  "${KEYCLOAK_URL}/admin/realms/${REALM}/clients" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "zt-frontend-client",
    "name": "ZT Frontend Application",
    "enabled": true,
    "publicClient": true,
    "standardFlowEnabled": true,
    "implicitFlowEnabled": false,
    "directAccessGrantsEnabled": true,
    "redirectUris": ["http://localhost:3000/*"],
    "webOrigins": ["http://localhost:3000"],
    "attributes": {
      "pkce.code.challenge.method": "S256",
      "access.token.lifespan": "300"
    },
    "defaultClientScopes": ["openid", "profile", "email", "did"],
    "optionalClientScopes": ["roles"]
  }'

# Création du client backend
echo "Création du client backend..."
curl -s -X POST \
  "${KEYCLOAK_URL}/admin/realms/${REALM}/clients" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "zt-backend-client",
    "name": "ZT Backend API",
    "enabled": true,
    "publicClient": false,
    "secret": "'"${KEYCLOAK_CLIENT_SECRET}"'",
    "serviceAccountsEnabled": true,
    "standardFlowEnabled": false,
    "directAccessGrantsEnabled": false,
    "bearerOnly": true
  }'

echo "Clients créés avec succès."