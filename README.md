# Zero Trust Decentralized IAM System

> **Decentralized Identity & Access Management** combining Zero Trust Architecture, Ethereum Blockchain, and AES-256-GCM End-to-End Encryption — built entirely on open-source tools.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.19-purple?logo=ethereum)](https://soliditylang.org)
[![Keycloak](https://img.shields.io/badge/Keycloak-23.x-orange)](https://keycloak.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🔐 What This Project Solves

Traditional IAM systems (Active Directory, centralized Keycloak, Okta) share a **critical structural flaw**: a single point of failure. When the identity server is compromised, the entire system is exposed — as demonstrated by SolarWinds (2020), Okta (2022–2023), and Colonial Pipeline (2021).

This project proposes and implements a **three-layer decentralized IAM architecture** that eliminates this vulnerability:

| Layer | Technology | Role |
|-------|-----------|------|
| **Layer 1 — Zero Trust IAM** | Keycloak + OAuth 2.0 + OIDC | Authentication, short-lived JWTs, MFA |
| **Layer 2 — Decentralized Registry** | Ethereum + Solidity smart contract | Immutable identity verification on-chain |
| **Layer 3 — E2E Encryption** | AES-256-GCM + OpenSSL | Confidentiality of all identity data |

**Core principle:** Access is granted only after passing **both** Layer 1 (Keycloak/ZTA) AND Layer 2 (Blockchain) validation. Trust is never implicit.

---

## 📊 Validated Performance Results

Evaluated against 4 reproducible attack scenarios on a controlled environment:

| Metric | Result | Threshold |
|--------|--------|-----------|
| **Attack Detection Rate** | **100%** (80/80 attacks blocked) | ≥ 90% |
| **False Positive Rate** | **0%** | ≤ 2% |
| **Avg. Authentication Latency** | **462 ms** | ≤ 2,000 ms |
| **System Availability under DoS** | **86%** | ≥ 80% |
| **Identity Revocation Time** | **< 5 minutes** | ≤ 10 min |
| **Throughput** | **15–16 auth/s** | ≥ 10 auth/s |

All 4 research hypotheses (H1–H4) validated. See [full evaluation](#evaluation) below.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   USER / CLIENT                      │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │   LAYER 1 — ZERO TRUST  │
          │   Keycloak (OAuth 2.0)  │
          │   MFA · PKCE · RBAC    │
          │   JWT (5 min TTL)       │
          └────────────┬────────────┘
                       │ Blockchain validation required
          ┌────────────▼────────────┐
          │   LAYER 2 — BLOCKCHAIN  │
          │   Ethereum (Hardhat)    │
          │   Solidity smart contract│
          │   IdentityRegistry.sol  │
          │   register/verify/revoke│
          └────────────┬────────────┘
                       │ Access granted only if verified
          ┌────────────▼────────────┐
          │   LAYER 3 — ENCRYPTION  │
          │   AES-256-GCM + OpenSSL │
          │   SHA-256 hash on-chain │
          │   Keys stored in Keycloak│
          └─────────────────────────┘
```

---

## 🚀 Quick Start

**Prerequisites:** Docker, Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/Heresia517/zerotrust-identity-system.git
cd zerotrust-identity-system

# 2. Launch all services (Keycloak, PostgreSQL, Hardhat, Redis, Vault, MinIO)
docker compose up -d

# 3. Wait ~30 seconds for services to initialize, then check status
bash check_project_status.sh
```

That's it. The full stack is running locally.

### Services Started

| Service | Port | Role |
|---------|------|------|
| Keycloak | 8080 | Zero Trust IAM (admin: admin/admin) |
| PostgreSQL | 5432 | Keycloak identity storage |
| Hardhat | 8545 | Local Ethereum node |
| Redis | 6379 | Session cache |
| Vault | 8200 | Key management |
| MinIO | 9000 | Off-chain encrypted storage |

---

## 📁 Project Structure

```
zerotrust-identity-system/
├── backend/                    # FastAPI backend
│   ├── auth/                   # OAuth 2.0 + Blockchain validation
│   ├── crypto/                 # AES-256-GCM module (crypto_service.py)
│   └── blockchain/             # Web3.py smart contract integration
├── contracts/                  # Solidity smart contracts
│   └── IdentityRegistry.sol    # Core identity registry (register/verify/revoke)
├── frontend/                   # React SPA
├── keycloak/scripts/           # Zero Trust realm auto-configuration
│   ├── setup_realm.sh          # Creates zt-decentralized-iam realm
│   └── setup_clients.sh        # OAuth2 clients with PKCE
├── tests/                      # Unit + integration tests
│   ├── test_smart_contract.js  # 17 Hardhat tests (all passing)
│   ├── test_crypto.py          # AES-256-GCM module tests
│   └── test_integration.py     # End-to-end integration test
└── docker-compose.yml          # One-command deployment
```

---

## 🔒 Security Features

### Zero Trust Implementation (NIST SP 800-207)
- **Short-lived tokens:** Access tokens expire in 5 minutes (vs. 1 hour in standard config)
- **Mandatory MFA:** TOTP required for all users
- **Brute-force protection:** Auto-lock after 5 failed attempts
- **Continuous verification:** Every request validated against the Blockchain registry

### Blockchain Identity Registry (Solidity 0.8.19)
```solidity
// Three core functions of the IdentityRegistry smart contract
function register(string memory did) external onlyAdmin
function verify(address userAddress) external view returns (bool)
function revoke(address userAddress) external onlyAdmin
```
- Immutable on-chain record: every registration/revocation is permanently logged
- SHA-256 hash of encrypted identity data stored on-chain for integrity verification
- W3C DID standard (`did:ethr:0x...`) for decentralized identifiers

### AES-256-GCM Encryption
- All identity data encrypted before off-chain storage
- GCM authentication tag detects any tampering (100% detection in tests)
- Encryption keys stored exclusively in Keycloak — never transmitted in API responses

---

## 🧪 Running Tests

```bash
# Smart contract tests (Hardhat)
cd contracts
npx hardhat test
# Expected: 17 tests passing

# Encryption module tests (Python)
pytest tests/test_crypto.py -v

# End-to-end integration test
pytest tests/test_integration.py -v
```

---

## ⚔️ Attack Scenarios Evaluated {#evaluation}

| Scenario | Attack Type | Detection | Result |
|----------|------------|-----------|--------|
| **A** | Token Replay (50 tokens, 4 delays) | Keycloak TTL + Blockchain | ✅ 100% blocked |
| **B** | DoS (1,000 simultaneous requests) | Brute-force protection | ✅ 86% availability maintained |
| **C** | JWT Forgery (RS256 bypass attempt) | Signature + `blockchain_verified` claim | ✅ 100% rejected |
| **D** | Traffic Interception (Wireshark) | AES-256-GCM + TLS 1.3 | ✅ 0% sensitive data visible |

---

## ⚙️ Configuration

The Zero Trust realm is auto-configured via script:

```bash
# Auto-configure Keycloak realm with Zero Trust policies
bash keycloak/scripts/setup_realm.sh

# Create OAuth2 clients (frontend with PKCE, backend confidential)
bash keycloak/scripts/setup_clients.sh
```

Key Zero Trust parameters applied:
- `accessTokenLifespan`: 300s (5 min)
- `refreshTokenMaxReuse`: 0 (single-use rotation)
- `bruteForceProtected`: true, max 5 failures
- `otpPolicyType`: totp (mandatory)

---

## 🔧 Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| IAM Server | Keycloak | 23.x |
| Backend API | FastAPI + Python | 3.11 |
| Frontend | React + Vite | 18.x |
| Blockchain | Ethereum (Hardhat) | local node |
| Smart Contract | Solidity | 0.8.19 |
| Blockchain Client | Web3.py | 6.x |
| Encryption | OpenSSL (AES-256-GCM) | system |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7.2 |
| Secret Management | HashiCorp Vault | 1.15 |
| Object Storage | MinIO | latest |
| Container | Docker Compose | v2 |

---

## 📚 Academic Context

This project was developed as part of a **Master's thesis in Information Security** at *Université Aube Nouvelle (ISIG)*, Ouagadougou, Burkina Faso (2025–2026).

**Thesis title:** *"Conception d'un Système Décentralisé de Gestion des Identités Numériques fondé sur le Modèle Zéro-Trust et la Blockchain"*

**Methodology:** Design Science Research (DSR) — systematic literature review, formal architecture design, prototype implementation, quantitative evaluation.

**Standards compliance:** NIST SP 800-207 (Zero Trust), W3C DID Core 1.0, OAuth 2.0 (RFC 6749), OpenID Connect, ISO/IEC 27001:2022.

---

## 🌍 Use Cases

This architecture is particularly relevant for:
- Organizations in **data-sensitive sectors** (healthcare, finance, government) seeking to eliminate IAM single points of failure
- **African institutions** building sovereign digital identity infrastructure on open-source tools
- Teams wanting to **migrate from centralized IAM** (Active Directory, Okta) toward a Zero Trust model
- Security researchers exploring **Blockchain + IAM integration** patterns

---

## 🗺️ Roadmap

- [ ] Redis cache for Blockchain verification (target: reduce latency from 462ms to ~20ms)
- [ ] Hyperledger Fabric migration (deterministic transaction times for production)
- [ ] W3C Verifiable Credentials integration
- [ ] Full Self-Sovereign Identity (SSI) mode — remove Keycloak SPOF
- [ ] Kubernetes deployment manifests
- [ ] Grafana dashboard for real-time security metrics

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to open an issue or submit a PR.

If you use this project in your research or organization, a ⭐ star helps others find it.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Hezekiah Toe TOPAN**
Master 2 — Information Security | Université Aube Nouvelle, Burkina Faso
Stage: YULCOM Technologies, Ouagadougou

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/hezekiah-topan)
[![GitHub](https://img.shields.io/badge/GitHub-Heresia517-black?logo=github)](https://github.com/Heresia517)

---

*Built with open-source tools only. Reproducible on any machine with Docker installed.*
