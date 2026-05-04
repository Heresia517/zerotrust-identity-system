# backend/app/models/user.py
"""
Modèle SQLAlchemy pour la table 'users'.
"""
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    did = Column(String(255), unique=True, nullable=True)  # Decentralized ID (peut être nul initialement)
    email = Column(String(255), unique=True, nullable=False)
    keycloak_id = Column(String(255), unique=True, nullable=False)  # ID de l'utilisateur Keycloak
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.email}>"