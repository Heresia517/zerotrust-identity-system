import pytest
import hashlib
from app.services.crypto_service import CryptoService, EncryptedData

class TestCryptoService:
    def test_encrypt_decrypt_nominal(self):
        key = CryptoService.generate_key()
        data = b"Identity: TOPAN Toe Hezekiah | Email: topan@univ.bf"
        encrypted = CryptoService.encrypt(data, key)
        decrypted = CryptoService.decrypt(encrypted, key)
        assert decrypted == data
        print("✓ AES-256-GCM encryption/decryption: OK")

    def test_ciphertext_tampering_detection(self):
        key = CryptoService.generate_key()
        data = b"Sensitive data"
        encrypted = CryptoService.encrypt(data, key)
        ct_tampered = bytearray(encrypted.ciphertext)
        ct_tampered[5] ^= 0xFF
        tampered_data = EncryptedData(
            ciphertext=bytes(ct_tampered),
            iv=encrypted.iv,
            hash_onchain=encrypted.hash_onchain
        )
        with pytest.raises(ValueError, match="Decryption failed"):
            CryptoService.decrypt(tampered_data, key)
        print("✓ GCM tampering detection: OK")

    def test_onchain_hash_verification(self):
        key = CryptoService.generate_key()
        data = b"Data to protect"
        encrypted = CryptoService.encrypt(data, key)
        assert CryptoService.verify_integrity(encrypted, encrypted.hash_onchain)
        print("✓ On-chain SHA-256 hash verification: OK")

    def test_key_uniqueness(self):
        keys = {CryptoService.generate_key() for _ in range(1000)}
        assert len(keys) == 1000
        print("✓ Key uniqueness: OK (1000/1000)")