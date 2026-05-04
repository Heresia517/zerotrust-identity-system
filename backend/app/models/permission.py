# backend/app/models/permission.py
"""
Modèle SQLAlchemy pour la table 'permissions'.
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id'), nullable=False)
    grantee_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    level = Column(String(50), nullable=False)  # "READ", "WRITE", "DELETE", "ADMIN"
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False)
    blockchain_hash = Column(String(66), nullable=True)  # Hash de la transaction/permission

    # Relations
    file = relationship("File", foreign_keys=[file_id])
    grantee = relationship("User", foreign_keys=[grantee_id])

    # Une seule permission active par (file, grantee, level) non révoquée ? 
    # On gère la logique dans le code, pas de contrainte unique stricte.

    def __repr__(self):
        return f"<Permission {self.level} for file {self.file_id} user {self.grantee_id}>"