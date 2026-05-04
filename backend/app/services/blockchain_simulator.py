import hashlib
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.audit_log import AuditLog
from datetime import datetime
import logging
from typing import Optional, Dict, Any
from web3 import Web3
from app.config import settings

logger = logging.getLogger(__name__)

CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"admin","type":"address"}],"name":"AdministrateurAjoute","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"utilisateur","type":"address"},{"indexed":False,"internalType":"string","name":"did","type":"string"},{"indexed":False,"internalType":"uint256","name":"date","type":"uint256"}],"name":"IdentiteEnregistree","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"utilisateur","type":"address"},{"indexed":False,"internalType":"uint256","name":"date","type":"uint256"}],"name":"IdentiteRevoquee","type":"event"},
    {"inputs":[{"internalType":"address","name":"utilisateur","type":"address"},{"internalType":"string","name":"did","type":"string"},{"internalType":"bytes32","name":"hashDonnees","type":"bytes32"}],"name":"enregistrer","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"utilisateur","type":"address"}],"name":"obtenirIdentite","outputs":[{"components":[{"internalType":"string","name":"did","type":"string"},{"internalType":"bool","name":"actif","type":"bool"},{"internalType":"uint256","name":"dateEnregistrement","type":"uint256"},{"internalType":"uint256","name":"dateRevocation","type":"uint256"},{"internalType":"bytes32","name":"hashDonneesChiffrees","type":"bytes32"}],"internalType":"struct IdentityRegistry.Identite","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"nombreIdentites","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"proprietaire","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"utilisateur","type":"address"}],"name":"revoquer","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"utilisateur","type":"address"}],"name":"verifier","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"}
]

CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

def get_contract():
    w3 = Web3(Web3.HTTPProvider(settings.ethereum_rpc_url))
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    contract.w3 = w3
    return contract

class BlockchainSimulator:
    @staticmethod
    def create_block(action: str, user_id: str, file_id: Optional[str] = None,
                     db: Optional[Session] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if db is None:
            logger.warning("Aucune session DB fournie, création ignorée")
            return None
        last_block = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).first()
        previous_hash = last_block.current_hash if last_block else ""
        block_data = {
            "action": action,
            "user_id": str(user_id) if user_id else None,
            "file_id": str(file_id) if file_id else None,
            "timestamp": datetime.utcnow().isoformat(),
            "data": metadata or {},
            "previous_hash": previous_hash
        }
        block_json = json.dumps(block_data, sort_keys=True).encode('utf-8')
        current_hash = hashlib.sha256(block_json).hexdigest()
        new_block = AuditLog(
            action=action,
            user_id=user_id,
            file_id=file_id,
            previous_hash=previous_hash,
            current_hash=current_hash,
            data=metadata or {}
        )
        db.add(new_block)
        db.commit()
        logger.info(f"Bloc créé: {current_hash} pour action {action}")
        return current_hash

    @staticmethod
    def verify_chain(db: Session) -> bool:
        blocks = db.query(AuditLog).order_by(AuditLog.timestamp).all()
        if not blocks:
            return True
        prev_hash = blocks[0].previous_hash
        if prev_hash != "":
            logger.error("Premier bloc invalide: previous_hash non vide")
            return False
        for i, block in enumerate(blocks):
            data_dict = {
                "action": block.action,
                "user_id": str(block.user_id) if block.user_id else None,
                "file_id": str(block.file_id) if block.file_id else None,
                "timestamp": block.timestamp.isoformat(),
                "data": block.data,
                "previous_hash": block.previous_hash
            }
            block_json = json.dumps(data_dict, sort_keys=True).encode('utf-8')
            expected_hash = hashlib.sha256(block_json).hexdigest()
            if block.current_hash != expected_hash:
                logger.error(f"Hash invalide pour le bloc {i}: {block.id}")
                return False
            if i > 0 and block.previous_hash != blocks[i-1].current_hash:
                logger.error(f"Lien rompu entre bloc {i-1} et {i}")
                return False
        return True
