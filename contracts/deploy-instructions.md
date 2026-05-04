# Déploiement du contrat Permissions.sol

Ce document explique comment déployer le contrat `Permissions.sol` sur un réseau Ethereum (local, testnet ou mainnet) et l'intégrer avec le backend du projet ZeroTrust.

## Prérequis

- **Node.js** (v16 ou supérieur) et npm/yarn
- Un wallet avec des fonds (pour les réseaux réels)
- **Hardhat** ou **Truffle** (ici nous utiliserons Hardhat)
- Accès à un nœud Ethereum (Infura, Alchemy, ou local avec Ganache)

## Installation

1. Créez un nouveau projet Hardhat (si ce n'est pas déjà fait) :
   ```bash
   mkdir zero-contracts
   cd zero-contracts
   npm init -y
   npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
   npx hardhat init