# backend/app/services/crypto_proxy.py
"""
Orchestration du chiffrement/déchiffrement des fichiers.
"""
import uuid
import hashlib
import logging
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from redis import Redis

from app.core.vault_client import VaultClient
from app.core.minio_client import MinIOClient
from app.services.permission_manager import PermissionManager
from app.services.blockchain_simulator import BlockchainSimulator
from app.models.file import File
from app.models.user import User
import os

logger = logging.getLogger(__name__)

class CryptoProxy:
    def __init__(self, vault: VaultClient, minio: MinIOClient, perm_mgr: PermissionManager):
        self.vault = vault
        self.minio = minio
        self.perm_mgr = perm_mgr

    async def upload_encrypted_file(
        self,
        file: UploadFile,
        user_id: uuid.UUID,
        db: Session,
        blockchain: BlockchainSimulator
    ) -> File:
        """
        Téléverse un fichier déjà chiffré côté client.
        Génère une clé de chiffrement (pour la démo) et la stocke dans Vault.
        """
        # Lire le contenu (déjà chiffré)
        content = await file.read()
        size = len(content)

        # Calculer le hash du contenu (pour vérification)
        file_hash = hashlib.sha256(content).hexdigest()

        # Générer un ID pour le fichier
        file_id = uuid.uuid4()

        # Chemin dans MinIO : {user_id}/{file_id}/{filename}
        object_path = f"{user_id}/{file_id}/{file.filename}"

        # Upload vers MinIO
        try:
            etag = self.minio.upload_file(object_path, content, file.content_type)
        except Exception as e:
            logger.error(f"Erreur upload MinIO: {e}")
            raise HTTPException(status_code=500, detail="Erreur lors de l'upload du fichier")

        # Générer une clé symétrique aléatoire (simulation)
        key = os.urandom(32)  # 256 bits
        # Stocker la clé dans Vault
        try:
            vault_path = self.vault.store_file_key(str(file_id), key)
        except Exception as e:
            logger.error(f"Erreur stockage clé dans Vault: {e}")
            # Nettoyer le fichier MinIO déjà uploadé
            self.minio.delete_file(object_path)
            raise HTTPException(status_code=500, detail="Erreur lors du stockage de la clé de chiffrement")

        # Créer l'entrée en base
        db_file = File(
            id=file_id,
            owner_id=user_id,
            name=file.filename,
            minio_path=object_path,
            vault_key_path=vault_path,
            file_hash=file_hash,
            size=size,
            encrypted=True
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # Enregistrer dans la blockchain
        try:
            blockchain.create_block(
                action="FILE_UPLOADED",
                user_id=user_id,
                file_id=file_id,
                metadata={"filename": file.filename, "size": size},
                db=db
            )
        except Exception as e:
            logger.warning(f"Impossible d'enregistrer dans blockchain: {e}")

        return db_file

    async def download_encrypted_file(
        self,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        db: Session,
        perm_mgr: PermissionManager,
        redis_client: Redis
    ) -> bytes:
        """
        Télécharge un fichier après vérification des permissions.
        Retourne le contenu chiffré (pas de déchiffrement côté serveur).
        """
        # Vérifier la permission de lecture
        if not perm_mgr.check_permission(file_id, user_id, "READ", db):
            raise HTTPException(status_code=403, detail="Permission refusée")

        # Récupérer les métadonnées du fichier
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="Fichier introuvable")

        # Télécharger depuis MinIO
        try:
            content = self.minio.download_file(file_record.minio_path)
        except Exception as e:
            logger.error(f"Erreur download MinIO: {e}")
            raise HTTPException(status_code=500, detail="Erreur lors du téléchargement du fichier")

        # Enregistrer l'accès dans la blockchain
        try:
            BlockchainSimulator.create_block(
                action="FILE_DOWNLOADED",
                user_id=user_id,
                file_id=file_id,
                metadata={},
                db=db
            )
        except Exception as e:
            logger.warning(f"Impossible d'enregistrer dans blockchain: {e}")

        return content