# backend/app/services/permission_manager.py
"""
Gestionnaire des permissions avec cache Redis.
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from redis import Redis
from app.models.file import File
from app.models.permission import Permission
from app.models.user import User
from app.services.blockchain_simulator import BlockchainSimulator
import logging

logger = logging.getLogger(__name__)

class PermissionManager:
    # Hiérarchie des niveaux de permission (en minuscules pour correspondre à la base)
    LEVEL_HIERARCHY = {
        "read": 0,
        "write": 1,
        "delete": 2,
        "admin": 3
    }

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def grant_permission(self, file_id: uuid.UUID, grantee_id: uuid.UUID, level: str,
                         duration: int, db: Session) -> Permission:
        """
        Accorde une permission sur un fichier.
        duration: durée en secondes (0 = illimité)
        """
        # Convertir le niveau en minuscules pour cohérence
        level = level.lower()
        # Vérifier que le fichier existe
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            raise ValueError("Fichier introuvable")

        # Vérifier que le niveau est valide
        if level not in self.LEVEL_HIERARCHY:
            raise ValueError(f"Niveau invalide: {level}")

        # Calcul de la date d'expiration
        expires_at = datetime.utcnow() + timedelta(seconds=duration) if duration > 0 else None

        # Créer la permission
        perm = Permission(
            file_id=file_id,
            grantee_id=grantee_id,
            level=level,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(perm)
        db.commit()
        db.refresh(perm)

        # Enregistrer dans la blockchain
        try:
            blockchain_hash = BlockchainSimulator.create_block(
                action="PERMISSION_GRANTED",
                user_id=grantee_id,
                file_id=file_id,
                metadata={"level": level, "duration": duration, "permission_id": str(perm.id)},
                db=db
            )
            perm.blockchain_hash = blockchain_hash
            db.commit()
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement blockchain: {e}")
            # On continue, la permission est créée mais non tracée

        # Invalider le cache pour cette combinaison
        cache_key = f"perm:{file_id}:{grantee_id}"
        self.redis.delete(cache_key)

        return perm

    def check_permission(self, file_id: uuid.UUID, user_id: uuid.UUID,
                         required_level: str, db: Session) -> bool:
        """
        Vérifie si l'utilisateur a le niveau requis sur le fichier.
        Utilise le cache Redis.
        """
        required_level = required_level.lower()
        # Niveau requis en int
        req_int = self.LEVEL_HIERARCHY.get(required_level)
        if req_int is None:
            return False

        cache_key = f"perm:{file_id}:{user_id}"

        # Essayer de récupérer depuis le cache
        cached_level = self.redis.get(cache_key)
        if cached_level is not None:
            # Le cache stocke le niveau max (en int)
            return int(cached_level) >= req_int

        # Sinon, interroger la base pour obtenir le niveau max
        now = datetime.utcnow()
        # Récupérer le niveau le plus élevé (max) parmi les permissions non révoquées et non expirées
        max_level = db.query(func.max(Permission.level)).filter(
            Permission.file_id == file_id,
            Permission.grantee_id == user_id,
            Permission.is_revoked == False,
            (Permission.expires_at == None) | (Permission.expires_at > now)
        ).scalar()

        if max_level is None:
            # Pas de permission
            self.redis.setex(cache_key, 300, -1)  # Cache négatif
            return False

        # Convertir le niveau max en entier
        max_int = self.LEVEL_HIERARCHY.get(max_level, -1)
        # Mettre en cache
        self.redis.setex(cache_key, 300, max_int)

        return max_int >= req_int

    def revoke_permission(self, permission_id: uuid.UUID, db: Session):
        """Révoque une permission et met à jour la blockchain."""
        perm = db.query(Permission).filter(Permission.id == permission_id).first()
        if not perm:
            raise ValueError("Permission introuvable")

        perm.is_revoked = True
        db.commit()

        # Enregistrer dans la blockchain
        try:
            blockchain_hash = BlockchainSimulator.create_block(
                action="PERMISSION_REVOKED",
                user_id=perm.grantee_id,
                file_id=perm.file_id,
                metadata={"permission_id": str(perm.id)},
                db=db
            )
            # On pourrait stocker le hash de révocation si on veut, mais on a déjà le hash original
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement blockchain: {e}")

        # Invalider le cache
        cache_key = f"perm:{perm.file_id}:{perm.grantee_id}"
        self.redis.delete(cache_key)