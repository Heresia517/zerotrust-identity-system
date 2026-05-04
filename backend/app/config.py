# backend/app/config.py
"""
Configuration de l'application à partir des variables d'environnement.
Utilise pydantic-settings pour valider et charger les paramètres.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Base de données
    database_url: str = Field(..., env='DATABASE_URL')

    # Keycloak
    keycloak_url: str = Field(..., env='KEYCLOAK_URL')
    keycloak_realm: str = Field(..., env='KEYCLOAK_REALM')
    keycloak_client_id: str = Field(..., env='KEYCLOAK_CLIENT_ID')
    keycloak_client_secret: str = Field(..., env='KEYCLOAK_CLIENT_SECRET')

    # Vault
    vault_url: str = Field(..., env='VAULT_URL')
    vault_token: str = Field(..., env='VAULT_TOKEN')
    vault_transit_key: str = Field(..., env='VAULT_TRANSIT_KEY')

    # MinIO
    minio_endpoint: str = Field(..., env='MINIO_ENDPOINT')
    minio_access_key: str = Field(..., env='MINIO_ACCESS_KEY')
    minio_secret_key: str = Field(..., env='MINIO_SECRET_KEY')
    minio_bucket_name: str = Field(..., env='MINIO_BUCKET_NAME')
    minio_secure: bool = Field(False, env='MINIO_SECURE')

    # Redis
    redis_url: str = Field(..., env='REDIS_URL')

    # Ethereum
    ethereum_rpc_url: Optional[str] = Field(None, env='ETHEREUM_RPC_URL')
    contract_address: Optional[str] = Field(None, env='CONTRACT_ADDRESS')

    # JWT local (optionnel, pour sessions internes)
    secret_key: str = Field(..., env='SECRET_KEY')
    algorithm: str = Field('HS256', env='ALGORITHM')

    class Config:
        env_file = '.env'
        case_sensitive = False

# Instance unique des paramètres
settings = Settings()