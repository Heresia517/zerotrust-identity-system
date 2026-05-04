import os, subprocess

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        # Affiche max 60 lignes par fichier
        preview = '\n'.join(lines[:60])
        truncated = len(lines) > 60
        return preview, truncated, len(lines)
    except Exception as e:
        return f"ERREUR: {e}", False, 0

files_to_read = [
    'docker-compose.yml',
    '.env',
    'contracts/Permissions.sol',
    'contracts/deploy-instructions.md',
    'backend/app/main.py',
    'backend/app/config.py',
    'backend/app/dependencies.py',
    'backend/app/core/security.py',
    'backend/app/core/vault_client.py',
    'backend/app/services/blockchain_simulator.py',
    'backend/app/services/crypto_proxy.py',
    'backend/app/api/auth.py',
    'backend/app/models/user.py',
    'backend/app/db/session.py',
    'frontend/src/App.jsx',
    'frontend/src/context/AuthContext.jsx',
    'frontend/src/components/Login.jsx',
    'frontend/src/services/api.js',
    'frontend/src/services/crypto.js',
    'backend/requirements.txt',
]

print("=" * 70)
print("AUDIT CONTENU DU PROJET")
print("=" * 70)

for fpath in files_to_read:
    print(f"\n{'='*70}")
    print(f"FILE: {fpath}")
    print(f"{'='*70}")
    if os.path.exists(fpath):
        content, truncated, total = read_file(fpath)
        print(content)
        if truncated:
            print(f"... [TRONQUÉ — {total} lignes au total]")
    else:
        print("❌ FICHIER MANQUANT")

print("\n" + "="*70)
print("STRUCTURE COMPLÈTE DU PROJET")
print("="*70)
for root, dirs, files in os.walk('.'):
    # Ignorer node_modules, __pycache__, .git
    dirs[:] = [d for d in dirs if d not in ['node_modules','__pycache__','.git','.venv','venv','dist','build']]
    level = root.replace('.', '').count(os.sep)
    indent = '  ' * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = '  ' * (level + 1)
    for f in files:
        size = os.path.getsize(os.path.join(root, f))
        print(f"{subindent}{f}  ({size} bytes)")