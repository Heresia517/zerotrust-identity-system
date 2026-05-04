# backend/app/services/key_manager.py
"""
Gestionnaire de clés AES-256 via les attributs utilisateur Keycloak.
Les clés sont stockées base64-encodées dans l'attribut 'aes_key'
du profil utilisateur Keycloak, accessible uniquement via l'API admin.
"""
import requests
import base64
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class KeyManager:
    def __init__(self, keycloak_url: str, realm: str, admin_token: str):
        self.base_url = f"{keycloak_url}/admin/realms/{realm}/users"
        self.headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

    def stocker_cle(self, user_id: str, cle: bytes) -> bool:
        """Stocke une clé AES-256 dans les attributs Keycloak de l'utilisateur"""
        try:
            cle_b64 = base64.b64encode(cle).decode()
            payload = {"attributes": {"aes_key": [cle_b64]}}
            resp = requests.put(f"{self.base_url}/{user_id}", json=payload, headers=self.headers)
            if resp.status_code in (200, 204):
                logger.info(f"Clé stockée pour l'utilisateur {user_id}")
                return True
            else:
                logger.error(f"Erreur stockage clé: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Exception lors du stockage de la clé: {e}")
            return False

    def recuperer_cle(self, user_id: str) -> Optional[bytes]:
        """Récupère la clé AES-256 d'un utilisateur depuis Keycloak"""
        try:
            resp = requests.get(f"{self.base_url}/{user_id}", headers=self.headers)
            if resp.status_code != 200:
                logger.warning(f"Utilisateur {user_id} non trouvé ou erreur {resp.status_code}")
                return None
            attributs = resp.json().get('attributes', {})
            cle_b64 = attributs.get('aes_key', [None])[0]
            if not cle_b64:
                logger.warning(f"Aucune clé trouvée pour l'utilisateur {user_id}")
                return None
            return base64.b64decode(cle_b64)
        except Exception as e:
            logger.error(f"Exception lors de la récupération de la clé: {e}")
            return None

    def revoquer_cle(self, user_id: str) -> bool:
        """Supprime la clé AES-256 lors de la révocation d'une identité"""
        try:
            payload = {"attributes": {"aes_key": []}}
            resp = requests.put(f"{self.base_url}/{user_id}", json=payload, headers=self.headers)
            if resp.status_code in (200, 204):
                logger.info(f"Clé révoquée pour l'utilisateur {user_id}")
                return True
            else:
                logger.error(f"Erreur révocation clé: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Exception lors de la révocation de la clé: {e}")
            return False