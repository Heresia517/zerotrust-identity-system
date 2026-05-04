"""
AES-256-GCM encryption service for identity data protection.
Uses the `cryptography` library (OpenSSL backend).
"""

import os
import hashlib
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dataclasses import dataclass
from typing import Optional

@dataclass
class EncryptedData:
    """Container for encrypted data and its metadata"""
    ciphertext: bytes    # Encrypted data (includes GCM tag)
    iv: bytes            # Initialization vector (96 bits)
    hash_onchain: bytes  # SHA-256 of ciphertext (stored on-chain)
    version: str = "AES-256-GCM-v1"

class CryptoService:
    """
    End-to-end encryption service for identity data.
    Uses AES-256-GCM (NIST FIPS 197 + SP 800-38D).
    """
    KEY_SIZE_BYTES = 32   # 256 bits
    IV_SIZE_BYTES  = 12   # 96 bits (recommended for GCM)

    @staticmethod
    def generate_key() -> bytes:
        """Generates a secure random AES-256 key."""
        return os.urandom(CryptoService.KEY_SIZE_BYTES)

    @staticmethod
    def encrypt(data: bytes, key: bytes,
                associated_data: Optional[bytes] = None) -> EncryptedData:
        """
        Encrypts data with AES-256-GCM.
        Associated data (AAD) is authenticated but not encrypted.
        """
        if len(key) != CryptoService.KEY_SIZE_BYTES:
            raise ValueError(f"Invalid key length: {len(key)} bytes (expected {CryptoService.KEY_SIZE_BYTES})")
        iv = os.urandom(CryptoService.IV_SIZE_BYTES)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, data, associated_data)
        # Compute SHA-256 hash for on-chain storage
        hash_onchain = hashlib.sha256(ciphertext).digest()
        return EncryptedData(
            ciphertext=ciphertext,
            iv=iv,
            hash_onchain=hash_onchain,
        )

    @staticmethod
    def decrypt(encrypted_data: EncryptedData, key: bytes,
                associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypts data with AES-256-GCM and verifies integrity.
        Raises ValueError if the GCM tag is invalid (data tampered).
        """
        aesgcm = AESGCM(key)
        try:
            return aesgcm.decrypt(
                encrypted_data.iv,
                encrypted_data.ciphertext,
                associated_data
            )
        except Exception:
            raise ValueError("Decryption failed: data corrupted or incorrect key")

    @staticmethod
    def verify_integrity(encrypted_data: EncryptedData,
                         hash_onchain: bytes) -> bool:
        """
        Verifies that the ciphertext matches the on-chain SHA-256 hash.
        Detects off-chain data tampering.
        """
        current_hash = hashlib.sha256(encrypted_data.ciphertext).digest()
        return current_hash == hash_onchain

    @staticmethod
    def serialize(encrypted_data: EncryptedData) -> str:
        """Serializes to JSON (bytes are base64-encoded)."""
        import base64
        return json.dumps({
            'ciphertext': base64.b64encode(encrypted_data.ciphertext).decode(),
            'iv': base64.b64encode(encrypted_data.iv).decode(),
            'hash_onchain': base64.b64encode(encrypted_data.hash_onchain).decode(),
            'version': encrypted_data.version,
        })