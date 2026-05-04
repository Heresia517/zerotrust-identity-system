"""
integration-backend.py
Script d'intégration du smart contract Permissions.sol avec le backend FastAPI.
Permet d'enregistrer un fichier sur la blockchain et de gérer les permissions on-chain.

Usage:
    python integration-backend.py --action register --file-id 1
    python integration-backend.py --action grant --file-id 1 --grantee 0xADRESSE --level 1
    python integration-backend.py --action check --file-id 1 --grantee 0xADRESSE
    python integration-backend.py --action verify
"""

import os
import sys
import argparse
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv(Path(__file__).parent.parent / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ── Tentative d'import web3 ───────────────────────────────────────────────────
try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("web3 non installé — mode simulation activé")

# ── Configuration ─────────────────────────────────────────────────────────────
RPC_URL          = os.getenv('ETHEREUM_RPC_URL', 'http://localhost:8545')
PRIVATE_KEY      = os.getenv('ETHEREUM_PRIVATE_KEY', '')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '')

# ABI minimal du contrat Permissions.sol
ABI = [
    {
        "inputs": [],
        "name": "registerFile",
        "outputs": [{"internalType": "uint256","name": "fileId","type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256","name": "fileId","type": "uint256"},
            {"internalType": "address","name": "grantee","type": "address"},
            {"internalType": "uint8","name": "level","type": "uint8"},
            {"internalType": "uint256","name": "expiresAt","type": "uint256"}
        ],
        "name": "grantPermission",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256","name": "fileId","type": "uint256"},
            {"internalType": "address","name": "grantee","type": "address"}
        ],
        "name": "revokePermission",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256","name": "fileId","type": "uint256"},
            {"internalType": "address","name": "grantee","type": "address"},
            {"internalType": "uint8","name": "requiredLevel","type": "uint8"}
        ],
        "name": "hasPermission",
        "outputs": [{"internalType": "bool","name": "","type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,"internalType": "uint256","name": "fileId","type": "uint256"},
            {"indexed": True,"internalType": "address","name": "owner","type": "address"},
            {"indexed": False,"internalType": "uint256","name": "timestamp","type": "uint256"}
        ],
        "name": "FileRegistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,"internalType": "uint256","name": "fileId","type": "uint256"},
            {"indexed": True,"internalType": "address","name": "grantee","type": "address"},
            {"indexed": False,"internalType": "uint8","name": "level","type": "uint8"},
            {"indexed": False,"internalType": "uint256","name": "expiresAt","type": "uint256"},
            {"indexed": False,"internalType": "uint256","name": "timestamp","type": "uint256"}
        ],
        "name": "PermissionGranted",
        "type": "event"
    }
]

PERMISSION_LEVELS = {
    0: "NONE", 1: "READ", 2: "WRITE", 3: "DELETE", 4: "ADMIN"
}

# ── Connexion Web3 ─────────────────────────────────────────────────────────────
def get_web3():
    if not WEB3_AVAILABLE:
        return None
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        logger.warning(f"Impossible de se connecter à {RPC_URL} — mode simulation")
        return None
    logger.info(f"✅ Connecté au nœud Ethereum : {RPC_URL}")
    logger.info(f"   Dernier bloc : #{w3.eth.block_number}")
    return w3

def get_contract(w3):
    if not w3 or not CONTRACT_ADDRESS or CONTRACT_ADDRESS == '0xAdresseDuContratDeploye':
        return None
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=ABI
        )
        logger.info(f"✅ Contrat chargé : {CONTRACT_ADDRESS}")
        return contract
    except Exception as e:
        logger.error(f"Erreur chargement contrat : {e}")
        return None

# ── Actions ───────────────────────────────────────────────────────────────────
def action_register(w3, contract, args):
    """Enregistre un nouveau fichier sur la blockchain."""
    if not contract:
        logger.info("[SIMULATION] registerFile() → fileId = 42")
        print(json.dumps({"status": "simulated", "fileId": 42, "txHash": "0xSIMULATED"}))
        return

    account = w3.eth.account.from_key(PRIVATE_KEY)
    tx = contract.functions.registerFile().build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Décoder l'événement FileRegistered pour récupérer le fileId
    logs = contract.events.FileRegistered().process_receipt(receipt)
    file_id = logs[0]['args']['fileId'] if logs else None

    result = {
        "status": "success",
        "fileId": file_id,
        "txHash": tx_hash.hex(),
        "blockNumber": receipt['blockNumber'],
        "gasUsed": receipt['gasUsed']
    }
    logger.info(f"✅ Fichier enregistré — fileId={file_id} — tx={tx_hash.hex()[:20]}...")
    print(json.dumps(result))

def action_grant(w3, contract, args):
    """Accorde une permission sur un fichier."""
    file_id   = int(args.file_id)
    grantee   = args.grantee
    level     = int(args.level)
    expires   = int(args.expires) if args.expires else 0

    if not contract:
        logger.info(f"[SIMULATION] grantPermission(fileId={file_id}, grantee={grantee}, level={PERMISSION_LEVELS.get(level, level)}, expiresAt={expires})")
        print(json.dumps({"status": "simulated", "fileId": file_id, "grantee": grantee, "level": level}))
        return

    account = w3.eth.account.from_key(PRIVATE_KEY)
    tx = contract.functions.grantPermission(
        file_id,
        Web3.to_checksum_address(grantee),
        level,
        expires
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    result = {
        "status": "success",
        "fileId": file_id,
        "grantee": grantee,
        "level": PERMISSION_LEVELS.get(level, level),
        "txHash": tx_hash.hex(),
        "blockNumber": receipt['blockNumber']
    }
    logger.info(f"✅ Permission accordée — {result}")
    print(json.dumps(result))

def action_check(w3, contract, args):
    """Vérifie si une adresse a une permission sur un fichier."""
    file_id  = int(args.file_id)
    grantee  = args.grantee
    level    = int(args.level) if args.level else 1

    if not contract:
        logger.info(f"[SIMULATION] hasPermission(fileId={file_id}, grantee={grantee}, level={level}) → True")
        print(json.dumps({"status": "simulated", "hasPermission": True, "level": PERMISSION_LEVELS.get(level, level)}))
        return

    has_perm = contract.functions.hasPermission(
        file_id,
        Web3.to_checksum_address(grantee),
        level
    ).call()

    result = {
        "status": "success",
        "fileId": file_id,
        "grantee": grantee,
        "requiredLevel": PERMISSION_LEVELS.get(level, level),
        "hasPermission": has_perm
    }
    logger.info(f"{'✅' if has_perm else '❌'} Permission check — {result}")
    print(json.dumps(result))

def action_verify(w3, contract, args):
    """Vérifie la connexion et l'état du contrat."""
    print("\n" + "="*60)
    print("VÉRIFICATION DE L'INTÉGRATION BLOCKCHAIN")
    print("="*60)
    print(f"  RPC_URL          : {RPC_URL}")
    print(f"  CONTRACT_ADDRESS : {CONTRACT_ADDRESS or '⚠️  NON CONFIGURÉ'}")
    print(f"  PRIVATE_KEY      : {'✅ Configurée' if PRIVATE_KEY and PRIVATE_KEY != '0xVOTRE_CLE_PRIVEE_SANS_0x' else '⚠️  Non configurée'}")
    print(f"  web3.py          : {'✅ Installé' if WEB3_AVAILABLE else '❌ Non installé'}")

    if w3:
        print(f"  Connexion nœud   : ✅ OK (bloc #{w3.eth.block_number})")
        if contract:
            print(f"  Contrat          : ✅ Chargé")
            try:
                counter = contract.functions.fileCounter().call()
                print(f"  fileCounter      : {counter} fichiers enregistrés")
            except Exception as e:
                print(f"  Contrat call     : ⚠️  {e}")
        else:
            print(f"  Contrat          : ⚠️  Non chargé (adresse manquante ou invalide)")
    else:
        print(f"  Connexion nœud   : ⚠️  Impossible — mode simulation actif")

    print("="*60)
    print("MODE : " + ("BLOCKCHAIN RÉELLE" if w3 and contract else "SIMULATION (PostgreSQL)"))
    print("="*60 + "\n")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Intégration smart contract Permissions.sol ↔ Backend ZeroTrust"
    )
    parser.add_argument('--action', required=True,
                        choices=['register','grant','revoke','check','verify'],
                        help="Action à effectuer")
    parser.add_argument('--file-id',  type=str, help="ID du fichier (uint256)")
    parser.add_argument('--grantee',  type=str, help="Adresse Ethereum du bénéficiaire")
    parser.add_argument('--level',    type=str, default='1',
                        help="Niveau de permission : 0=NONE 1=READ 2=WRITE 3=DELETE 4=ADMIN")
    parser.add_argument('--expires',  type=str, default='0',
                        help="Timestamp d'expiration Unix (0 = jamais)")

    args = parser.parse_args()

    w3       = get_web3()
    contract = get_contract(w3)

    actions = {
        'register': action_register,
        'grant':    action_grant,
        'check':    action_check,
        'verify':   action_verify,
    }

    action_fn = actions.get(args.action)
    if action_fn:
        action_fn(w3, contract, args)
    else:
        logger.error(f"Action inconnue : {args.action}")
        sys.exit(1)

if __name__ == '__main__':
    main()
