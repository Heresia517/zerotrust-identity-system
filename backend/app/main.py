"""
Point d'entrée de l'application FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import logging

from app.api import auth, files, permissions, blockchain
from app.db.session import engine
from app.models import user, file, permission
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZeroTrust File Management API",
    description="Backend pour la gestion de fichiers chiffrés avec architecture Zero-Trust",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(permissions.router)
app.include_router(blockchain.router)

@app.get("/")
async def health_check():
    return {"status": "healthy"}

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.on_event("startup")
async def startup_event():
    logger.info("Démarrage du backend...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connexion PostgreSQL OK")
    except Exception as e:
        logger.error(f"Erreur connexion PostgreSQL: {e}")
    logger.info("Backend prêt")