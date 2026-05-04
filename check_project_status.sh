#!/bin/bash
# Script : check_project_status.sh
# Description : Vérifie l'état réel des composants du projet IAM décentralisé Zéro-Trust
# Adapté pour détecter automatiquement les conteneurs par port

set -euo pipefail

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    local component=$1
    local status=$2
    local details=$3
    if [ "$status" == "OK" ]; then
        echo -e "${GREEN}✓ $component : $details${NC}"
    elif [ "$status" == "WARN" ]; then
        echo -e "${YELLOW}⚠ $component : $details${NC}"
    else
        echo -e "${RED}✗ $component : $details${NC}"
    fi
}

# Trouve un conteneur par port publié
find_container_by_port() {
    local port=$1
    docker ps --filter "publish=$port" --format "{{.Names}}" | head -n1
}

# 1. Vérification de Docker
echo "=== 1. Vérification de Docker ==="
if ! command -v docker &> /dev/null; then
    print_status "Docker" "FAIL" "Docker non installé"
    exit 1
fi
if ! docker info &> /dev/null; then
    print_status "Docker" "FAIL" "Docker ne tourne pas"
    exit 1
fi

# 2. Détection des services par ports
echo -e "\n=== 2. Services Docker ==="
keycloak_container=$(find_container_by_port 8080)
postgres_container=$(find_container_by_port 5432)
hardhat_container=$(find_container_by_port 8545)
redis_container=$(find_container_by_port 6379)
vault_container=$(find_container_by_port 8200)
minio_container=$(find_container_by_port 9000)

[ -n "$keycloak_container" ] && print_status "Keycloak" "OK" "conteneur: $keycloak_container" || print_status "Keycloak" "FAIL" "aucun conteneur exposant le port 8080"
[ -n "$postgres_container" ] && print_status "PostgreSQL" "OK" "conteneur: $postgres_container" || print_status "PostgreSQL" "FAIL" "aucun conteneur exposant le port 5432"
[ -n "$hardhat_container" ] && print_status "Hardhat" "OK" "conteneur: $hardhat_container" || print_status "Hardhat" "FAIL" "aucun conteneur exposant le port 8545"
[ -n "$redis_container" ] && print_status "Redis" "OK" "conteneur: $redis_container" || print_status "Redis" "WARN" "aucun conteneur exposant le port 6379"
[ -n "$vault_container" ] && print_status "Vault" "OK" "conteneur: $vault_container" || print_status "Vault" "WARN" "aucun conteneur exposant le port 8200"
[ -n "$minio_container" ] && print_status "MinIO" "OK" "conteneur: $minio_container" || print_status "MinIO" "WARN" "aucun conteneur exposant le port 9000"

# 3. Keycloak : disponibilité, realm, clients
echo -e "\n=== 3. Keycloak (IAM) ==="
KEYCLOAK_URL="http://localhost:8080"
REALM="zt-decentralized-iam"

# Lire les identifiants depuis .env s'il existe
if [ -f ".env" ]; then
    source .env
fi
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-Admin@ZT2024!}"

if curl -s -o /dev/null -w "%{http_code}" "$KEYCLOAK_URL" | grep -q "200\|302"; then
    print_status "Keycloak" "OK" "service accessible"
    # Obtenir token admin
    TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "client_id=admin-cli&username=$ADMIN_USER&password=$ADMIN_PASS&grant_type=password" \
        | jq -r '.access_token')
    if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
        print_status "Keycloak admin" "FAIL" "impossible d'obtenir un token admin (identifiants incorrects ?)"
    else
        print_status "Keycloak admin" "OK" "token récupéré"
        REALM_EXISTS=$(curl -s -H "Authorization: Bearer $TOKEN" "$KEYCLOAK_URL/admin/realms/$REALM" | jq -r '.realm // empty')
        if [ "$REALM_EXISTS" == "$REALM" ]; then
            print_status "Realm $REALM" "OK" "existe"
        else
            print_status "Realm $REALM" "FAIL" "non trouvé"
        fi
    fi
else
    print_status "Keycloak" "FAIL" "service injoignable"
fi

# 4. Blockchain (Hardhat)
echo -e "\n=== 4. Blockchain (Hardhat) ==="
HARDHAT_RPC="http://localhost:8545"
if curl -s -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' "$HARDHAT_RPC" | jq -e '.result' &>/dev/null; then
    print_status "Hardhat RPC" "OK" "répond"
else
    print_status "Hardhat RPC" "FAIL" "ne répond pas"
fi

CONTRACT_CONFIG="contracts/contract-config.json"
if [ -f "$CONTRACT_CONFIG" ]; then
    CONTRACT_ADDR=$(jq -r '.contractAddress // empty' "$CONTRACT_CONFIG")
    if [ -n "$CONTRACT_ADDR" ]; then
        print_status "Smart contract" "OK" "adresse trouvée : $CONTRACT_ADDR"
        BLOCKCHAIN_CHECK=$(curl -s -X POST -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_call\",\"params\":[{\"to\":\"$CONTRACT_ADDR\",\"data\":\"0x9e7672c9\"},\"latest\"],\"id\":1}" "$HARDHAT_RPC" | jq -r '.result // empty')
        if [ -n "$BLOCKCHAIN_CHECK" ]; then
            print_status "Smart contract" "OK" "fonction nombreIdentites accessible"
        else
            print_status "Smart contract" "WARN" "adresse trouvée mais appel échoue (peut-être pas déployé ?)"
        fi
    else
        print_status "Smart contract" "WARN" "fichier de configuration trouvé mais adresse vide"
    fi
else
    print_status "Smart contract" "WARN" "fichier contract-config.json absent"
fi

# 5. Module de chiffrement
echo -e "\n=== 5. Module de chiffrement ==="
if command -v python3 &> /dev/null; then
    if [ -f "backend/app/services/crypto_service.py" ]; then
        python3 - <<EOF
import sys
sys.path.insert(0, 'backend')
from app.services.crypto_service import CryptoService

try:
    key = CryptoService.generate_key()
    data = b"test data"
    encrypted = CryptoService.encrypt(data, key)
    decrypted = CryptoService.decrypt(encrypted, key)
    assert decrypted == data
    print("OK")
except Exception as e:
    print("FAIL")
    print(e)
    sys.exit(1)
EOF
        if [ $? -eq 0 ]; then
            print_status "CryptoService" "OK" "chiffrement/déchiffrement fonctionne"
        else
            print_status "CryptoService" "FAIL" "test échoué"
        fi
    else
        print_status "CryptoService" "WARN" "fichier crypto_service.py non trouvé"
    fi
else
    print_status "Python3" "WARN" "non installé, impossible de tester le module de chiffrement"
fi

# 6. Scripts d'intégration
echo -e "\n=== 6. Scripts d'intégration ==="
INTEGRATION_SCRIPT="backend/app/api/auth.py"
if [ -f "$INTEGRATION_SCRIPT" ]; then
    if grep -q "verifier_identite_blockchain" "$INTEGRATION_SCRIPT" || grep -q "blockchain" "$INTEGRATION_SCRIPT"; then
        print_status "Intégration Blockchain" "OK" "script d'authentification avec Blockchain trouvé"
    else
        print_status "Intégration Blockchain" "WARN" "script trouvé mais pas de référence à la Blockchain"
    fi
else
    print_status "Intégration Blockchain" "WARN" "fichier $INTEGRATION_SCRIPT absent"
fi

# 7. Tests unitaires Hardhat
echo -e "\n=== 7. Tests unitaires Hardhat ==="
if [ -d "contracts" ] && [ -d "contracts/test" ]; then
    if [ -d "contracts/node_modules" ]; then
        if [ -f "contracts/test/IdentityRegistry.test.js" ]; then
            (cd contracts && npx hardhat test 2>&1 | grep -q "passing" && echo "OK" || echo "FAIL") > /tmp/test_result
            if grep -q "OK" /tmp/test_result; then
                print_status "Tests unitaires Hardhat" "OK" "exécutés avec succès"
            else
                print_status "Tests unitaires Hardhat" "FAIL" "l'exécution a échoué"
            fi
        else
            print_status "Tests unitaires Hardhat" "WARN" "fichier de test absent"
        fi
    else
        print_status "Tests unitaires Hardhat" "WARN" "node_modules non trouvés"
    fi
else
    print_status "Tests unitaires Hardhat" "WARN" "répertoire contracts/test non trouvé"
fi

# 8. Fichiers de configuration
echo -e "\n=== 8. Fichiers de configuration ==="
[ -f "docker-compose.yml" ] && print_status "docker-compose.yml" "OK" "présent" || print_status "docker-compose.yml" "FAIL" "absent"
[ -f ".env" ] && print_status ".env" "OK" "présent" || print_status ".env" "WARN" "absent (peut causer des problèmes de variables)"

echo -e "\n=== RÉSUMÉ FINAL ==="