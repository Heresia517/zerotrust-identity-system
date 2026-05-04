# backend/app/db/session.py
"""
Configuration de la session SQLAlchemy.
Fournit une dépendance get_db() pour FastAPI.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Création du moteur SQLAlchemy
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # Vérifie la connexion avant utilisation
    echo=False            # Mettre à True pour voir les requêtes SQL en debug
)

# Session locale pour les interactions avec la base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles déclaratifs
Base = declarative_base()

def get_db():
    """
    Dépendance FastAPI pour obtenir une session de base de données.
    Yields: Session SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()