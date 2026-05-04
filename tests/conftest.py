import pytest
from web3 import Web3
import requests
import json
import os

@pytest.fixture(scope='session')
def keycloak_admin_token():
    """Token admin du realm master pour créer/modifier les utilisateurs."""
    response = requests.post(
        'http://localhost:8080/realms/master/protocol/openid-connect/token',
        data={
            'client_id': 'admin-cli',
            'username': 'admin',
            'password': 'admin123',
            'grant_type': 'password'
        }
    )
    response.raise_for_status()
    return response.json()['access_token']


@pytest.fixture(scope='session')
def realm_admin_token(keycloak_admin_token):
    """
    Token d'un utilisateur admin dans le realm 'zt-decentralized-iam'.
    Crée l'utilisateur 'adminzt' avec le rôle 'ROLE_ADMIN' si nécessaire.
    """
    realm = "zt-decentralized-iam"
    admin_username = "adminzt"
    admin_password = "admin123"

    headers = {"Authorization": f"Bearer {keycloak_admin_token}"}

    # Vérifier si l'utilisateur existe déjà
    url_users = f"http://localhost:8080/admin/realms/{realm}/users?username={admin_username}"
    resp = requests.get(url_users, headers=headers)
    resp.raise_for_status()
    users = resp.json()
    if not users:
        # Créer l'utilisateur
        user_payload = {
            "username": admin_username,
            "enabled": True,
            "emailVerified": True,
            "credentials": [{"type": "password", "value": admin_password, "temporary": False}]
        }
        resp_create = requests.post(f"http://localhost:8080/admin/realms/{realm}/users", json=user_payload, headers=headers)
        resp_create.raise_for_status()
        user_id = resp_create.headers["Location"].split("/")[-1]

        # Récupérer l'ID du rôle ROLE_ADMIN
        roles_url = f"http://localhost:8080/admin/realms/{realm}/roles"
        resp_roles = requests.get(roles_url, headers=headers)
        resp_roles.raise_for_status()
        role_id = None
        for role in resp_roles.json():
            if role["name"] == "ROLE_ADMIN":
                role_id = role["id"]
                break
        if not role_id:
            # Créer le rôle s'il n'existe pas
            role_payload = {"name": "ROLE_ADMIN"}
            resp_role_create = requests.post(roles_url, json=role_payload, headers=headers)
            resp_role_create.raise_for_status()
            role_id = resp_role_create.json()["id"]

        # Assigner le rôle à l'utilisateur
        assign_url = f"http://localhost:8080/admin/realms/{realm}/users/{user_id}/role-mappings/realm"
        role_mapping = [{"id": role_id, "name": "ROLE_ADMIN"}]
        resp_assign = requests.post(assign_url, json=role_mapping, headers=headers)
        resp_assign.raise_for_status()

    # Obtenir le token pour cet utilisateur
    token_resp = requests.post(
        f"http://localhost:8080/realms/{realm}/protocol/openid-connect/token",
        data={
            "client_id": "zt-frontend-client",
            "username": admin_username,
            "password": admin_password,
            "grant_type": "password"
        }
    )
    token_resp.raise_for_status()
    return token_resp.json()["access_token"]


@pytest.fixture(scope='session')
def keycloak_user_id(keycloak_admin_token):
    """
    Récupère l'ID de l'utilisateur 'testuser' dans le realm 'zt-decentralized-iam'.
    """
    headers = {"Authorization": f"Bearer {keycloak_admin_token}"}
    url = "http://localhost:8080/admin/realms/zt-decentralized-iam/users?username=testuser"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    users = resp.json()
    if not users:
        raise ValueError("Utilisateur 'testuser' non trouvé dans Keycloak")
    return users[0]['id']


@pytest.fixture(scope='session')
def contrat_ethereum():
    """
    Fournit une instance du smart contract IdentityRegistry déployé sur Hardhat.
    """
    root_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(root_dir, 'contracts', 'contract-config.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Fichier {config_path} manquant. Déployez d'abord le contrat.")
    with open(config_path) as f:
        config = json.load(f)
    
    w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
    if not w3.is_connected():
        raise ConnectionError("Impossible de se connecter au nœud Hardhat (http://localhost:8545)")
    
    abi_path = os.path.join(root_dir, 'contracts', 'artifacts', 'contracts',
                            'IdentityRegistry.sol', 'IdentityRegistry.json')
    with open(abi_path) as f:
        abi = json.load(f)['abi']
    
    contract = w3.eth.contract(address=config['contractAddress'], abi=abi)
    contract.w3 = w3
    return contract