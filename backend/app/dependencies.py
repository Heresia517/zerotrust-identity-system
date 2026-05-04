# backend/app/dependencies.py
"""
Dépendances globales pour FastAPI.
"""
from redis import Redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def get_redis():
    """
    Retourne un client Redis connecté.
    """
    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        # Vérifier la connexion
        redis_client.ping()
        yield redis_client
    except Exception as e:
        logger.error(f"Impossible de se connecter à Redis: {e}")
        raise
    finally:
        redis_client.close()