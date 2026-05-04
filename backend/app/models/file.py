# backend/app/models/file.py
"""
Modèle SQLAlchemy pour la table 'files'.
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class File(Base):
    __tablename__ = 'files'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    minio_path = Column(String(512), nullable=False)      # Chemin dans le bucket MinIO
    vault_key_path = Column(String(512), nullable=False)  # Chemin de la clé dans Vault
    file_hash = Column(String(64), nullable=False)        # SHA-256 du fichier chiffré
    size = Column(BigInteger, nullable=False)
    encrypted = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relation avec l'utilisateur propriétaire
    owner = relationship("User", foreign_keys=[owner_id])

    def __repr__(self):
        return f"<File {self.name} owned by {self.owner_id}>"