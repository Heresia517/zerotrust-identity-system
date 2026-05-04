#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script d'audit pour le projet ZeroTrust.
Exécutez-le à la racine du projet pour vérifier quels fichiers sont présents.
"""

import os
import sys
from pathlib import Path

# Structure complète attendue (chemins relatifs à la racine du projet)
EXPECTED_FILES = {
    "RACINE": [
        "docker-compose.yml",
        "init-db.sql",
        ".env",
    ],
    "BACKEND": [
        "backend/Dockerfile",
        "backend/.dockerignore",
        "backend/requirements.txt",
        "backend/app/__init__.py",
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/dependencies.py",
        "backend/app/api/__init__.py",
        "backend/app/api/auth.py",
        "backend/app/api/files.py",
        "backend/app/api/permissions.py",
        "backend/app/core/__init__.py",
        "backend/app/core/security.py",
        "backend/app/core/vault_client.py",
        "backend/app/core/minio_client.py",
        "backend/app/models/__init__.py",
        "backend/app/models/user.py",
        "backend/app/models/file.py",
        "backend/app/models/permission.py",
        "backend/app/services/__init__.py",
        "backend/app/services/blockchain_simulator.py",
        "backend/app/services/permission_manager.py",
        "backend/app/services/crypto_proxy.py",
        "backend/app/services/crypto_service.py",  # AJOUTÉ
        "backend/app/db/__init__.py",
        "backend/app/db/session.py",
    ],
    "FRONTEND": [
        "frontend/Dockerfile",
        "frontend/.dockerignore",
        "frontend/package.json",
        "frontend/vite.config.js",
        "frontend/index.html",
        "frontend/src/main.jsx",
        "frontend/src/App.jsx",
        "frontend/src/App.css",
        "frontend/src/context/AuthContext.jsx",
        "frontend/src/components/Login.jsx",
        "frontend/src/components/Dashboard.jsx",
        "frontend/src/components/FileUpload.jsx",
        "frontend/src/components/FileList.jsx",
        "frontend/src/components/FileShare.jsx",
        "frontend/src/components/ProtectedRoute.jsx",
        "frontend/src/services/api.js",
        "frontend/src/services/crypto.js",
    ],
    "CONTRACTS": [
        "contracts/Permissions.sol",
        "contracts/deploy-instructions.md",
        "contracts/integration-backend.py",
    ]
}

def audit_project(root_path="."):
    """Vérifie l'existence des fichiers attendus dans root_path."""
    results = {}
    total_present = 0
    total_expected = 0

    print("═" * 60)
    print("AUDIT COMPLET DU PROJET")
    print("═" * 60)

    for category, files in EXPECTED_FILES.items():
        print(f"\n📁 {category} :")
        category_present = 0
        for rel_path in files:
            full_path = Path(root_path) / rel_path
            exists = full_path.exists()
            if exists:
                status = "✅"
                category_present += 1
                total_present += 1
            else:
                status = "❌"
            print(f"{status} {rel_path} - {'PRÉSENT' if exists else 'MANQUANT'}")
            total_expected += 1
        results[category] = category_present

    print("\n" + "═" * 60)
    print("RÉSUMÉ :")
    print("═" * 60)
    for category, count in results.items():
        total_cat = len(EXPECTED_FILES[category])
        print(f"{category} : {count}/{total_cat} fichiers présents")
    print("-" * 40)
    print(f"Total fichiers attendus : {total_expected}")
    print(f"Fichiers présents : {total_present} ✅")
    print(f"Fichiers manquants : {total_expected - total_present} ❌")
    if total_expected > 0:
        taux = (total_present / total_expected) * 100
        print(f"Taux de complétion : {taux:.1f}%")
    else:
        print("Taux de complétion : N/A")
    print("═" * 60)

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    if not os.path.isdir(root):
        print(f"Erreur : le répertoire '{root}' n'existe pas.")
        sys.exit(1)
    audit_project(root)

if __name__ == "__main__":
    main()