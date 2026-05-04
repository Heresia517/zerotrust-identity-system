# backend/app/models/audit_log.py
"""
Modèle SQLAlchemy pour la table 'audit_logs'.
"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(100), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    file_id = Column(UUID(as_uuid=True), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    previous_hash = Column(String(64), nullable=True)
    current_hash = Column(String(64), nullable=False)
    data = Column(JSON, nullable=True)