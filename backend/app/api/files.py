from app.models.user import User
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from redis import Redis
import uuid
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.vault_client import VaultClient
from app.core.minio_client import MinIOClient
from app.services.crypto_proxy import CryptoProxy
from app.services.permission_manager import PermissionManager
from app.services.blockchain_simulator import BlockchainSimulator
from app.models.file import File as FileModel
from app.models.permission import Permission
from app.dependencies import get_redis
import logging

router = APIRouter(prefix="/files", tags=["fichiers"])
logger = logging.getLogger(__name__)

def get_vault_client():
    return VaultClient()

def get_minio_client():
    return MinIOClient()

def get_perm_manager(redis: Redis = Depends(get_redis)):
    return PermissionManager(redis)

def get_crypto_proxy(
    vault: VaultClient = Depends(get_vault_client),
    minio: MinIOClient = Depends(get_minio_client),
    perm_mgr: PermissionManager = Depends(get_perm_manager)
):
    return CryptoProxy(vault, minio, perm_mgr)

@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    crypto: CryptoProxy = Depends(get_crypto_proxy),
    blockchain: BlockchainSimulator = Depends()
):
    keycloak_id = current_user.get("sub")
    user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    try:
        file_record = await crypto.upload_encrypted_file(
            file=file,
            user_id=user.id,
            db=db,
            blockchain=blockchain
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'upload: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'upload")

    return {
        "id": str(file_record.id),
        "name": file_record.name,
        "size": file_record.size,
        "created_at": file_record.created_at.isoformat()
    }

@router.get("/{file_id}")
async def download_file(
    file_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    crypto: CryptoProxy = Depends(get_crypto_proxy),
    redis: Redis = Depends(get_redis),
    perm_mgr: PermissionManager = Depends(get_perm_manager)
):
    keycloak_id = current_user.get("sub")
    user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    if not perm_mgr.check_permission(file_id, user.id, "read", db):
        logger.warning(f"Permission refusée pour user {user.id} sur fichier {file_id}")
        raise HTTPException(status_code=403, detail="Permission refusée")

    try:
        content = await crypto.download_encrypted_file(
            file_id=file_id,
            user_id=user.id,
            db=db,
            perm_mgr=perm_mgr,
            redis_client=redis
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du download: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors du téléchargement")

    from fastapi.responses import Response
    return Response(content=content, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={file_record.name}"})

@router.get("/", response_model=List[dict])
async def list_files(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keycloak_id = current_user.get("sub")
    user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    owned = db.query(FileModel).filter(FileModel.owner_id == user.id).all()
    now = datetime.utcnow()
    shared = db.query(FileModel).join(Permission, Permission.file_id == FileModel.id).filter(
        Permission.grantee_id == user.id,
        Permission.is_revoked == False,
        (Permission.expires_at == None) | (Permission.expires_at > now)
    ).all()

    files_dict = {str(f.id): f for f in owned}
    for f in shared:
        files_dict.setdefault(str(f.id), f)

    result = []
    for f in files_dict.values():
        result.append({
            "id": str(f.id),
            "name": f.name,
            "size": f.size,
            "created_at": f.created_at.isoformat(),
            "owner_id": str(f.owner_id),
            "encrypted": f.encrypted
        })
    return result

@router.delete("/{file_id}")
async def delete_file(
    file_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    vault: VaultClient = Depends(get_vault_client),
    minio: MinIOClient = Depends(get_minio_client),
    perm_mgr: PermissionManager = Depends(get_perm_manager),
    redis: Redis = Depends(get_redis)
):
    keycloak_id = current_user.get("sub")
    user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    if not perm_mgr.check_permission(file_id, user.id, "delete", db):
        if str(file_record.owner_id) != str(user.id):
            raise HTTPException(status_code=403, detail="Permission refusée")

    try:
        minio.delete_file(file_record.minio_path)
    except Exception as e:
        logger.error(f"Erreur suppression MinIO: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression du fichier")

    try:
        vault.delete_file_key(str(file_id))
    except Exception as e:
        logger.error(f"Erreur suppression clé Vault: {e}")

    db.delete(file_record)
    db.commit()

    try:
        BlockchainSimulator.create_block(
            action="FILE_DELETED",
            user_id=user.id,
            file_id=file_id,
            metadata={},
            db=db
        )
    except Exception as e:
        logger.warning(f"Impossible d'enregistrer dans blockchain: {e}")

    return {"message": "Fichier supprimé avec succès"}