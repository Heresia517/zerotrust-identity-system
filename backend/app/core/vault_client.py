# backend/app/core/vault_client.py
"""
Client pour HashiCorp Vault.
Utilise le backend transit pour chiffrer/déchiffrer les clés.
"""
import requests
import base64
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VaultClient:
    """
    Singleton pour interagir avec Vault.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        try:
            self.base_url = settings.vault_url.rstrip('/')
            self.token = settings.vault_token
            self.transit_key = settings.vault_transit_key
            # Vérifier l'authentification
            headers = {"X-Vault-Token": self.token}
            resp = requests.get(f"{self.base_url}/v1/sys/health", headers=headers)
            resp.raise_for_status()
            logger.info("Client Vault initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur initialisation Vault: {e}")
            raise

    def _encrypt_data(self, plaintext: bytes) -> str:
        """Chiffre des données avec la clé transit."""
        url = f"{self.base_url}/v1/transit/encrypt/{self.transit_key}"
        headers = {"X-Vault-Token": self.token}
        payload = {"plaintext": base64.b64encode(plaintext).decode('utf-8')}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["data"]["ciphertext"]

    def _decrypt_data(self, ciphertext: str) -> bytes:
        """Déchiffre des données avec la clé transit."""
        url = f"{self.base_url}/v1/transit/decrypt/{self.transit_key}"
        headers = {"X-Vault-Token": self.token}
        payload = {"ciphertext": ciphertext}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        plaintext_b64 = response.json()["data"]["plaintext"]
        return base64.b64decode(plaintext_b64)

    def store_file_key(self, file_id: str, key: bytes) -> str:
        """
        Chiffre la clé symétrique avec la clé transit et la stocke dans le KV.
        Retourne le chemin où la clé chiffrée est stockée.
        """
        try:
            ciphertext = self._encrypt_data(key)
        except Exception as e:
            logger.error(f"Erreur chiffrement clé avec Vault: {e}")
            raise

        # Stocker le ciphertext dans le KV v2 (sous secret/file-keys)
        path = f"file-keys/{file_id}"
        url = f"{self.base_url}/v1/secret/data/{path}"
        headers = {"X-Vault-Token": self.token, "Content-Type": "application/json"}
        payload = {"data": {"ciphertext": ciphertext}}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Erreur stockage clé dans Vault KV: {e}")
            raise

        return path

    def get_file_key(self, file_id: str) -> bytes:
        """
        Récupère le ciphertext depuis le KV, le déchiffre et retourne la clé en clair.
        """
        path = f"file-keys/{file_id}"
        url = f"{self.base_url}/v1/secret/data/{path}"
        headers = {"X-Vault-Token": self.token}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            ciphertext = response.json()["data"]["data"]["ciphertext"]
        except Exception as e:
            logger.error(f"Erreur lecture clé dans Vault: {e}")
            raise

        try:
            key = self._decrypt_data(ciphertext)
        except Exception as e:
            logger.error(f"Erreur déchiffrement clé avec Vault: {e}")
            raise

        return key

    def delete_file_key(self, file_id: str):
        """Supprime la clé associée au fichier."""
        path = f"file-keys/{file_id}"
        url = f"{self.base_url}/v1/secret/metadata/{path}"
        headers = {"X-Vault-Token": self.token}
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Erreur suppression clé dans Vault: {e}")
            raise