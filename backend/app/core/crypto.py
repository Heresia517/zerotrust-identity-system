"""
Module de chiffrement AES-256-GCM côté backend.
Utilisé par crypto_proxy.py pour chiffrer/déchiffrer les fichiers.
"""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import logging

logger = logging.getLogger(__name__)

def generate_key() -> bytes:
    """Génère une clé AES-256 aléatoire (32 bytes)."""
    return os.urandom(32)

def encrypt(data: bytes, key: bytes) -> tuple[bytes, bytes]:
    """
    Chiffre les données avec AES-256-GCM.
    Retourne (ciphertext, iv).
    """
    iv = os.urandom(12)  # 96 bits — recommandé GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data, None)
    logger.debug(f"Chiffrement AES-256-GCM OK — taille: {len(data)} → {len(ciphertext)} bytes")
    return ciphertext, iv

def decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """
    Déchiffre les données avec AES-256-GCM.
    Lève une exception si le tag d'authentification est invalide.
    """
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, ciphertext, None)
    logger.debug(f"Déchiffrement AES-256-GCM OK — taille: {len(ciphertext)} → {len(plaintext)} bytes")
    return plaintext

def hash_sha256(data: bytes) -> str:
    """Calcule le SHA-256 d'un contenu binaire."""
    import hashlib
    return hashlib.sha256(data).hexdigest()
