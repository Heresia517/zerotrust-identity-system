# backend/app/core/minio_client.py
"""
Client pour MinIO.
"""
from io import BytesIO
from minio import Minio
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MinIOClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        try:
            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure
            )
            # Vérifier que le bucket existe
            if not self.client.bucket_exists(settings.minio_bucket_name):
                self.client.make_bucket(settings.minio_bucket_name)
                logger.info(f"Bucket {settings.minio_bucket_name} créé")
            else:
                logger.info(f"Bucket {settings.minio_bucket_name} existe déjà")
        except Exception as e:
            logger.error(f"Erreur initialisation MinIO: {e}")
            raise

    def upload_file(self, object_path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Upload un fichier vers MinIO.
        Retourne l'etag (hash du fichier).
        """
        try:
            # Convertir les bytes en un flux BytesIO (qui a .read())
            data_stream = BytesIO(data)
            result = self.client.put_object(
                bucket_name=settings.minio_bucket_name,
                object_name=object_path,
                data=data_stream,
                length=len(data),
                content_type=content_type
            )
            return result.etag
        except Exception as e:
            logger.error(f"Erreur upload MinIO: {e}")
            raise

    def download_file(self, object_path: str) -> bytes:
        """Télécharge un fichier depuis MinIO et retourne son contenu en bytes."""
        try:
            response = self.client.get_object(
                bucket_name=settings.minio_bucket_name,
                object_name=object_path
            )
            data = response.read()
            response.close()
            return data
        except Exception as e:
            logger.error(f"Erreur download MinIO: {e}")
            raise

    def delete_file(self, object_path: str):
        """Supprime un objet du bucket."""
        try:
            self.client.remove_object(
                bucket_name=settings.minio_bucket_name,
                object_name=object_path
            )
        except Exception as e:
            logger.error(f"Erreur suppression MinIO: {e}")
            raise