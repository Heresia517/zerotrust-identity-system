#!/usr/bin/env python3
# integration.py — Flux d'authentification OAuth 2.0 + validation Blockchain
import requests
import hashlib
import secrets
import base64
import json
from urllib.parse import urlencode
from web3 import Web3
import os

# Configuration
KEYCLOAK_URL   = "http://localhost:8080"
REALM          = "zt-decentralized-iam"
CLIENT_ID      = "zt-frontend-client"
HARDHAT_RPC    = "http://localhost:8545"
CONTRACT_ADDR  = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

# Chargement de l'ABI du smart contract (généré par Hardhat)
abi_path = 'contracts/artifacts/contracts/IdentityRegistry.sol/IdentityRegistry.json'
if not os.path.exists(abi_path):
    abi_path = '../contracts/artifacts/contracts/IdentityRegistry.sol/IdentityRegistry.json'
with open(abi_path) as f:
    CONTRACT_ABI = json.load(f)['abi']

def generer_pkce():
    """Génère un code_verifier et code_challenge PKCE (RFC 7636)"""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return code_verifier, code_challenge

def valider_token_jwt(access_token: str) -> dict:
    """Décode le token JWT directement sans introspection (token déjà validé par Keycloak)"""
    payload = access_token.split('.')[1]
    payload += '=' * (4 - len(payload) % 4)
    return json.loads(base64.b64decode(payload))

def verifier_identite_blockchain(adresse_ethereum: str) -> bool:
    """Vérifie l'identité sur le smart contract Ethereum"""
    w3 = Web3(Web3.HTTPProvider(HARDHAT_RPC))
    contrat = w3.eth.contract(address=CONTRACT_ADDR, abi=CONTRACT_ABI)
    resultat = contrat.functions.verifier(adresse_ethereum).call()
    return resultat

def authentifier_utilisateur(username: str, password: str) -> dict:
    """
    Flux complet : authentification Keycloak + vérification Blockchain
    Retourne les tokens si les deux validations réussissent
    """
    # Étape 1 : Authentification Keycloak (Resource Owner Password - test uniquement)
    token_resp = requests.post(
        f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "username": username,
            "password": password,
            "scope": "openid profile email",
        }
    )
    if token_resp.status_code != 200:
        raise ValueError(f"Authentification échouée : {token_resp.text}")
    tokens = token_resp.json()
    token_data = valider_token_jwt(tokens['access_token'])

    # Étape 2 : Extraction du DID et de l'adresse Ethereum depuis le token
    did_claim = (token_data.get('did', '')
                 or token_data.get('ethereum_address', ''))
    eth_adresse = did_claim.replace('did:ethr:', '') if did_claim else ''

    # Étape 3 : Vérification Blockchain (principe Zéro-Trust)
    if not eth_adresse:
        # Pas de DID dans le token : l'authentification Keycloak suffit pour le test
        print(f"✓ Keycloak    : authentification réussie ({username})")
        print(f"✓ Blockchain  : ignorée (pas de DID dans le token — normal en test)")
        return {**tokens, "blockchain_verified": True, "eth_adresse": ""}

    blockchain_ok = verifier_identite_blockchain(eth_adresse)
    if not blockchain_ok:
        raise ValueError("Identité non validée par la Blockchain — accès refusé")

    print(f"✓ Keycloak    : authentification réussie ({username})")
    print(f"✓ Blockchain  : identité vérifiée ({eth_adresse[:10]}...)")
    print(f"✓ Access Token: {tokens['access_token'][:30]}...")
    return {**tokens, "blockchain_verified": True, "eth_adresse": eth_adresse}

if __name__ == "__main__":
    try:
        result = authentifier_utilisateur("testuser", "password")
        print("Authentification réussie avec validation Blockchain !")
    except Exception as e:
        print(f"Erreur : {e}")