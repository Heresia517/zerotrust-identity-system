# backend/app/api/permissions.py
"""
Routes de gestion des permissions.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from redis import Redis
import uuid
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.core.security import get_current_user
from app.services.permission_manager import PermissionManager
from app.services.blockchain_simulator import BlockchainSimulator
from app.models.user import User
from app.models.file import File
from app.models.permission import Permission
from app.dependencies import get_redis
import logging

router = APIRouter(prefix="/permissions", tags=["permissions"])
logger = logging.getLogger(__name__)

# Schémas Pydantic
class GrantPermissionRequest(BaseModel):
    file_id: uuid.UUID
    grantee_email: str
    level: str  # "read", "write", "delete", "admin"
    duration: int  # secondes, 0 = illimité

class RevokePermissionRequest(BaseModel):
    permission_id: uuid.UUID

class PermissionResponse(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    grantee_id: uuid.UUID
    level: str
    granted_at: str
    expires_at: Optional[str]
    is_revoked: bool
    blockchain_hash: Optional[str]

def get_perm_manager(redis: Redis = Depends(get_redis)):
    return PermissionManager(redis)

@router.post("/grant", response_model=PermissionResponse)
async def grant_permission(
    request: GrantPermissionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm_mgr: PermissionManager = Depends(get_perm_manager)
):
    """
    Accorde une permission sur un fichier.
    L'utilisateur courant doit être propriétaire du fichier.
    """
    keycloak_id = current_user.get("sub")
    user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    file = db.query(File).filter(File.id == request.file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    # Conversion en string pour éviter les problèmes de type UUID
    if str(file.owner_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Vous n'êtes pas propriétaire de ce fichier")

    grantee = db.query(User).filter(User.email == request.grantee_email).first()
    if not grantee:
        raise HTTPException(status_code=404, detail="Utilisateur bénéficiaire introuvable")

    try:
        perm = perm_mgr.grant_permission(
            file_id=request.file_id,
            grantee_id=grantee.id,
            level=request.level.lower(),
            duration=request.duration,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de l'octroi de permission: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

    return PermissionResponse(
        id=perm.id,
        file_id=perm.file_id,
        grantee_id=perm.grantee_id,
        level=perm.level,
        granted_at=perm.granted_at.isoformat(),
        expires_at=perm.expires_at.isoformat() if perm.expires_at else None,
        is_revoked=perm.is_revoked,
        blockchain_hash=perm.blockchain_hash
    )

@router.post("/revoke")
async def revoke_permission(
    request: RevokePermissionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm_mgr: PermissionManager = Depends(get_perm_manager)
):
    keycloak_id = current_user.get("sub")
    user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    perm = db.query(Permission).filter(Permission.id == request.permission_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail="Permission introuvable")

    file = db.query(File).filter(File.id == perm.file_id).first()
    if str(file.owner_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Vous n'êtes pas propriétaire de ce fichier")

    try:
        perm_mgr.revoke_permission(request.permission_id, db)
    except Exception as e:
        logger.error(f"Erreur lors de la révocation: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

    return {"message": "Permission révoquée"}

@router.get("/file/{file_id}", response_model=List[PermissionResponse])
async def get_file_permissions(
    file_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keycloak_id = current_user.get("sub")
    user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    if str(file.owner_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Accès refusé")

    perms = db.query(Permission).filter(Permission.file_id == file_id).all()
    return [
        PermissionResponse(
            id=p.id,
            file_id=p.file_id,
            grantee_id=p.grantee_id,
            level=p.level,
            granted_at=p.granted_at.isoformat(),
            expires_at=p.expires_at.isoformat() if p.expires_at else None,
            is_revoked=p.is_revoked,
            blockchain_hash=p.blockchain_hash
        ) for p in perms
    ]