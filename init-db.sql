-- Création des utilisateurs (idempotente)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'keycloak') THEN
      CREATE USER keycloak WITH PASSWORD 'keycloak123' CREATEDB;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'zerotrust') THEN
      CREATE USER zerotrust WITH PASSWORD 'zerotrust123' CREATEDB;
   END IF;
END
$$;

-- Création des bases (idempotente)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak') THEN
      CREATE DATABASE keycloak OWNER keycloak;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'zerotrust') THEN
      CREATE DATABASE zerotrust OWNER zerotrust;
   END IF;
END
$$;

-- Connexion à la base zerotrust
\c zerotrust

-- Activation de l'extension UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tables du backend (exemple minimal – adaptez selon votre modèle)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    did VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    minio_path VARCHAR(512) NOT NULL,
    vault_key_path VARCHAR(512) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    size BIGINT NOT NULL,
    encrypted BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_files_owner_id ON files(owner_id);

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    grantee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    level VARCHAR(50) NOT NULL CHECK (level IN ('read', 'write', 'admin')),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_revoked BOOLEAN DEFAULT FALSE,
    blockchain_hash VARCHAR(66),
    UNIQUE(file_id, grantee_id, level)
);
CREATE INDEX IF NOT EXISTS idx_permissions_file_id ON permissions(file_id);
CREATE INDEX IF NOT EXISTS idx_permissions_grantee_id ON permissions(grantee_id);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    file_id UUID REFERENCES files(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL,
    metadata JSONB
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_file_id ON audit_logs(file_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);

-- Fonction de calcul du hash d'audit
CREATE OR REPLACE FUNCTION compute_audit_hash()
RETURNS TRIGGER AS $$
DECLARE
    prev_hash VARCHAR(64);
    row_data TEXT;
BEGIN
    SELECT current_hash INTO prev_hash
    FROM audit_logs
    WHERE (file_id = NEW.file_id OR (NEW.file_id IS NULL AND file_id IS NULL))
    ORDER BY timestamp DESC
    LIMIT 1;
    IF prev_hash IS NULL THEN prev_hash := ''; END IF;
    NEW.previous_hash := prev_hash;
    row_data := COALESCE(NEW.id::TEXT, '') || '|' ||
                COALESCE(NEW.action, '') || '|' ||
                COALESCE(NEW.user_id::TEXT, '') || '|' ||
                COALESCE(NEW.file_id::TEXT, '') || '|' ||
                COALESCE(NEW.timestamp::TEXT, '') || '|' ||
                COALESCE(prev_hash, '') || '|' ||
                COALESCE(NEW.metadata::TEXT, '');
    NEW.current_hash := encode(sha256(row_data::bytea), 'hex');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger (recréé proprement)
DROP TRIGGER IF EXISTS trg_audit_logs_hash ON audit_logs;
CREATE TRIGGER trg_audit_logs_hash
    BEFORE INSERT ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION compute_audit_hash();