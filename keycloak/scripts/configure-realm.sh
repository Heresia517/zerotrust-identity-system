#!/bin/bash
# configure-realm.sh — Configuration automatique du realm Zéro-Trust
# conforme au mémoire (Chapitre II, Tableau 5)

set -euo pipefail

# Couleurs pour messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ----------------------------------------------------------------------
# 1. Chargement des variables d'environnement
# ----------------------------------------------------------------------
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo -e "${YELLOW}⚠️  Fichier .env non trouvé, utilisation des valeurs par défaut.${NC}"
fi

KEYCLOAK_URL="http://localhost:8080"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-Admin@ZT2024!}"
REALM="zt-decentralized-iam"
CLIENT_BACKEND_SECRET="69IouOOmUceYG8fgZOQbrQvnIkB6h4kR"

# ----------------------------------------------------------------------
# 2. Attente de Keycloak et obtention du token admin
# ----------------------------------------------------------------------
echo "⏳ Vérification de Keycloak..."
for i in {1..20}; do
    if curl -s -f "$KEYCLOAK_URL/realms/master" >/dev/null 2>&1; then
        break
    fi
    echo "   Tentative $i/20..."
    sleep 5
done

echo "🔐 Obtention du token admin..."
TOKEN_RESPONSE=$(curl -s -X POST \
    "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "client_id=admin-cli" \
    -d "username=$ADMIN_USER" \
    -d "password=$ADMIN_PASS" \
    -d "grant_type=password")

ADMIN_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
    echo -e "${RED}❌ Échec de l'obtention du token. Vérifiez les identifiants.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Token admin obtenu${NC}"

# ----------------------------------------------------------------------
# 3. Création du realm (idempotent)
# ----------------------------------------------------------------------
echo "📁 Création du realm '$REALM'..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "$KEYCLOAK_URL/admin/realms" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "realm": "'"$REALM"'",
        "displayName": "ZT Decentralized IAM",
        "enabled": true,
        "sslRequired": "external",
        "registrationAllowed": false,
        "loginWithEmailAllowed": true,
        "bruteForceProtected": true,
        "failureFactor": 5,
        "waitIncrementSeconds": 60,
        "accessTokenLifespan": 300,
        "ssoSessionIdleTimeout": 1800,
        "ssoSessionMaxLifespan": 36000,
        "offlineSessionIdleTimeout": 2592000,
        "passwordPolicy": "length(12) and upperCase(1) and digits(1) and specialChars(1) and notUsername"
    }')

case $HTTP_CODE in
    201) echo -e "${GREEN}✅ Realm créé${NC}" ;;
    409) echo -e "${YELLOW}⚠️  Realm existe déjà${NC}" ;;
    *) echo -e "${RED}❌ Erreur HTTP $HTTP_CODE lors de la création du realm${NC}" ; exit 1 ;;
esac

# ----------------------------------------------------------------------
# 4. Création des clients OAuth2 (Tableau 5)
# ----------------------------------------------------------------------
echo "🔧 Création des clients OAuth2..."

# Client backend (confidentiel, bearer-only)
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/clients" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "clientId": "zt-backend-client",
        "name": "ZT Backend API",
        "enabled": true,
        "publicClient": false,
        "serviceAccountsEnabled": true,
        "standardFlowEnabled": false,
        "directAccessGrantsEnabled": false,
        "bearerOnly": true,
        "secret": "'"$CLIENT_BACKEND_SECRET"'"
    }' >/dev/null 2>&1
echo "   zt-backend-client : créé (si non existant)"

# Client frontend (public, PKCE)
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/clients" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "clientId": "zt-frontend-client",
        "name": "ZT Frontend Application",
        "enabled": true,
        "publicClient": true,
        "standardFlowEnabled": true,
        "implicitFlowEnabled": false,
        "directAccessGrantsEnabled": false,
        "redirectUris": ["http://localhost:5173/*", "http://localhost:8000/*"],
        "webOrigins": ["http://localhost:5173", "http://localhost:8000"],
        "attributes": {
            "pkce.code.challenge.method": "S256",
            "access.token.lifespan": "300"
        },
        "defaultClientScopes": ["openid", "profile", "email"],
        "optionalClientScopes": ["roles"]
    }' >/dev/null 2>&1
echo "   zt-frontend-client : créé"

# Client admin (service account)
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/clients" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "clientId": "zt-admin-client",
        "name": "ZT Admin Client",
        "enabled": true,
        "serviceAccountsEnabled": true,
        "publicClient": false,
        "standardFlowEnabled": false,
        "directAccessGrantsEnabled": false
    }' >/dev/null 2>&1
echo "   zt-admin-client : créé"

# ----------------------------------------------------------------------
# 5. Création du scope personnalisé "did" et mapper
# ----------------------------------------------------------------------
echo "🔧 Configuration du scope 'did'..."

# Créer le scope
SCOPE_RESPONSE=$(curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/client-scopes" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
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
    }')

SCOPE_ID=$(echo "$SCOPE_RESPONSE" | jq -r '.id // empty')

if [ -n "$SCOPE_ID" ]; then
    # Ajouter le mapper (attribut ethereum_did → claim did)
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/client-scopes/$SCOPE_ID/protocol-mappers/models" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "did-claim-mapper",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "config": {
                "user.attribute": "ethereum_did",
                "claim.name": "did",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true"
            }
        }' >/dev/null 2>&1
    echo "   Scope 'did' et mapper créés"
else
    echo -e "${YELLOW}⚠️  Impossible de créer le scope 'did'${NC}"
fi

# Associer le scope au client frontend par défaut
FRONTEND_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$KEYCLOAK_URL/admin/realms/$REALM/clients?clientId=zt-frontend-client" | jq -r '.[0].id')
if [ -n "$FRONTEND_ID" ] && [ -n "$SCOPE_ID" ]; then
    curl -s -X PUT "$KEYCLOAK_URL/admin/realms/$REALM/clients/$FRONTEND_ID/default-client-scopes/$SCOPE_ID" \
        -H "Authorization: Bearer $ADMIN_TOKEN" >/dev/null 2>&1
    echo "   Scope 'did' associé au client frontend"
fi

# ----------------------------------------------------------------------
# 6. Création d'un utilisateur de test (avec attribut ethereum_did)
# ----------------------------------------------------------------------
echo "👤 Création de l'utilisateur testuser..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/users" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "email": "testuser@zerotrust.local",
        "enabled": true,
        "emailVerified": true,
        "credentials": [{"type": "password", "value": "testpass123", "temporary": false}],
        "attributes": {
            "ethereum_did": ["did:ethr:0x742d35Cc6634C0532925a3b8D4C9C8F3"]
        }
    }' >/dev/null 2>&1
echo -e "${GREEN}✅ Utilisateur testuser créé (mot de passe : testpass123)${NC}"

# ----------------------------------------------------------------------
# 7. Résumé final
# ----------------------------------------------------------------------
echo -e "\n${GREEN}========================================"
echo "✅ CONFIGURATION KEYCLOAK TERMINÉE"
echo "========================================"
echo "  Realm          : $REALM"
echo "  Clients        : zt-frontend-client, zt-backend-client, zt-admin-client"
echo "  Scope          : did (mapper ethereum_did → claim did)"
echo "  Utilisateur    : testuser / testpass123"
echo "  Token lifespan : 5 minutes (Zéro-Trust)"
echo "========================================${NC}"