from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentification"])

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    keycloak_id = current_user.get("sub")
    user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {
        "id": user.id,
        "email": user.email,
        "did": user.did,
        "keycloak_id": user.keycloak_id,
        "created_at": user.created_at
    }