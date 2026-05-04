import requests
import time
import os

BASE = "http://localhost:8080"
ADMIN_USER = os.getenv("KEYCLOAK_ADMIN", "admin")
ADMIN_PASS = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin123")
REALM = "zt-decentralized-iam"
CLIENT_FRONTEND = "zt-frontend-client"
CLIENT_BACKEND = "zt-backend-client"
CLIENT_ADMIN = "zt-admin-client"
CLIENT_SECRET_BACKEND = "69IouOOmUceYG8fgZOQbrQvnIkB6h4kR"
TEST_USER = "testuser"
TEST_PASS = "testpass123"

# --- Attente de Keycloak ---
print("⏳ Attente Keycloak...")
for i in range(20):
    try:
        r = requests.get(f"{BASE}/realms/master", timeout=3)
        if r.status_code == 200:
            print("✅ Keycloak prêt !")
            break
    except:
        pass
    print(f"  Tentative {i+1}/20...")
    time.sleep(5)

# --- Token admin ---
r = requests.post(
    f"{BASE}/realms/master/protocol/openid-connect/token",
    data={
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    }
)
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("✅ Token admin obtenu")

# --- Création du realm ---
r = requests.post(f"{BASE}/admin/realms", headers=H, json={
    "realm": REALM,
    "enabled": True,
    "displayName": "ZT Decentralized IAM",
    "accessTokenLifespan": 300,                 # 5 minutes (ZT)
    "ssoSessionIdleTimeout": 1800,              # 30 minutes
    "ssoSessionMaxLifespan": 36000,             # 10 heures
    "bruteForceProtected": True,                # Protection force brute
    "failureFactor": 5,                         # 5 tentatives
    "waitIncrementSeconds": 60,                 # Blocage progressif
    "passwordPolicy": "length(12) and upperCase(1) and digits(1) and specialChars(1) and notUsername",
    "registrationAllowed": False
})
print(f"✅ Realm {REALM} : {'créé' if r.status_code==201 else 'existe déjà' if r.status_code==409 else f'erreur {r.status_code}'}")

# --- Création du client backend (confidentiel, bearer-only) ---
r = requests.post(f"{BASE}/admin/realms/{REALM}/clients", headers=H, json={
    "clientId": CLIENT_BACKEND,
    "enabled": True,
    "secret": CLIENT_SECRET_BACKEND,
    "serviceAccountsEnabled": True,
    "publicClient": False,
    "bearerOnly": True,                         # Seul le flux client credentials est utilisé
    "standardFlowEnabled": False,
    "directAccessGrantsEnabled": False
})
print(f"✅ Client {CLIENT_BACKEND} : {'créé' if r.status_code==201 else 'existe déjà' if r.status_code==409 else f'erreur {r.status_code}'}")

# --- Création du client frontend (public, Authorization Code + PKCE) ---
r = requests.post(f"{BASE}/admin/realms/{REALM}/clients", headers=H, json={
    "clientId": CLIENT_FRONTEND,
    "enabled": True,
    "publicClient": True,
    "standardFlowEnabled": True,
    "implicitFlowEnabled": False,
    "directAccessGrantsEnabled": False,
    "redirectUris": ["http://localhost:5173/*", "http://localhost:8000/*"],
    "webOrigins": ["http://localhost:5173", "http://localhost:8000"],
    "attributes": {
        "pkce.code.challenge.method": "S256"
    }
})
print(f"✅ Client {CLIENT_FRONTEND} : {'créé' if r.status_code==201 else 'existe déjà' if r.status_code==409 else f'erreur {r.status_code}'}")

# --- Création du client admin (service account) ---
r = requests.post(f"{BASE}/admin/realms/{REALM}/clients", headers=H, json={
    "clientId": CLIENT_ADMIN,
    "enabled": True,
    "serviceAccountsEnabled": True,
    "publicClient": False,
    "standardFlowEnabled": False,
    "directAccessGrantsEnabled": False
})
print(f"✅ Client {CLIENT_ADMIN} : {'créé' if r.status_code==201 else 'existe déjà' if r.status_code==409 else f'erreur {r.status_code}'}")

# --- Création du scope personnalisé "did" ---
scope_name = "did"
r = requests.post(f"{BASE}/admin/realms/{REALM}/client-scopes", headers=H, json={
    "name": scope_name,
    "description": "Scope pour inclure le DID Ethereum dans les tokens JWT",
    "protocol": "openid-connect",
    "attributes": {
        "include.in.token.scope": "true",
        "display.on.consent.screen": "true",
        "consent.screen.text": "Accès à votre identifiant décentralisé (DID)"
    }
})
print(f"✅ Scope {scope_name} : {'créé' if r.status_code==201 else 'existe déjà' if r.status_code==409 else f'erreur {r.status_code}'}")

# --- Ajout du mapper pour l'attribut "ethereum_did" -> claim "did" ---
# D'abord récupérer l'ID du scope
scopes = requests.get(f"{BASE}/admin/realms/{REALM}/client-scopes", headers=H).json()
scope_id = None
for s in scopes:
    if s["name"] == scope_name:
        scope_id = s["id"]
        break
if scope_id:
    mapper_payload = {
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
    }
    r = requests.post(f"{BASE}/admin/realms/{REALM}/client-scopes/{scope_id}/protocol-mappers/models",
                      headers=H, json=mapper_payload)
    print(f"✅ Mapper pour scope {scope_name} : {'créé' if r.status_code==201 else 'existe déjà' if r.status_code==409 else f'erreur {r.status_code}'}")

# --- Associer le scope "did" aux clients (pour qu'il soit inclus dans les tokens) ---
# Pour le client frontend
clients = requests.get(f"{BASE}/admin/realms/{REALM}/clients", headers=H).json()
frontend_id = None
for c in clients:
    if c["clientId"] == CLIENT_FRONTEND:
        frontend_id = c["id"]
        break
if frontend_id and scope_id:
    # Ajouter le scope par défaut
    r = requests.put(f"{BASE}/admin/realms/{REALM}/clients/{frontend_id}/default-client-scopes/{scope_id}",
                     headers=H)
    print(f"✅ Scope {scope_name} ajouté au client {CLIENT_FRONTEND} : {r.status_code}")

# --- Création d'un utilisateur de test avec l'attribut ethereum_did ---
# L'utilisateur doit avoir un attribut "ethereum_did" qui sera mappé vers le claim "did"
r = requests.post(f"{BASE}/admin/realms/{REALM}/users", headers=H, json={
    "username": TEST_USER,
    "email": f"{TEST_USER}@zerotrust.local",
    "enabled": True,
    "emailVerified": True,
    "credentials": [{"type": "password", "value": TEST_PASS, "temporary": False}],
    "attributes": {
        "ethereum_did": ["did:ethr:0x742d35Cc6634C0532925a3b8D4C9C8F3"]  # Exemple
    }
})
print(f"✅ Utilisateur {TEST_USER} : {'créé' if r.status_code==201 else 'existe déjà' if r.status_code==409 else f'erreur {r.status_code}'}")

print("\n" + "="*60)
print("CONFIGURATION KEYCLOAK TERMINÉE (conforme au mémoire)")
print("="*60)
print(f"  Realm          : {REALM}")
print(f"  Clients        : {CLIENT_FRONTEND}, {CLIENT_BACKEND}, {CLIENT_ADMIN}")
print(f"  Scope          : {scope_name} (mapper attribut ethereum_did -> claim did)")
print(f"  Utilisateur    : {TEST_USER} / {TEST_PASS}")
print("="*60)