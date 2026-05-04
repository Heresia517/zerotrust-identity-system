from fastapi import Depends
from fastapi.security import OAuth2AuthorizationCodeBearer

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="http://localhost:8080/realms/zt-decentralized-iam/protocol/openid-connect/auth",
    tokenUrl="http://localhost:8080/realms/zt-decentralized-iam/protocol/openid-connect/token"
)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    return {
        "sub": "fb18e7e3-5604-4fa3-acf1-a973b580e013",
        "preferred_username": "testuser",
        "email": "testuser@zerotrust.local",
        "realm_access": {"roles": ["ROLE_ADMIN"]}
    }