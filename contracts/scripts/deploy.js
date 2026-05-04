// scripts/deploy.js — Déploiement du smart contract IdentityRegistry
const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");
async function main() {
  console.log("Déploiement du contrat IdentityRegistry...");
  // Récupération du compte déployeur (compte[0] Hardhat)
  const [deployeur] = await ethers.getSigners();
  console.log(`Déployeur : ${deployeur.address}`);
  console.log(
    `Solde     : ${ethers.formatEther(
      await deployeur.provider.getBalance(deployeur.address),
    )} ETH`,
  );
  // Compilation et déploiement
  const IdentityRegistry = await ethers.getContractFactory("IdentityRegistry");
  const contrat = await IdentityRegistry.deploy();
  await contrat.waitForDeployment();
  const adresseContrat = await contrat.getAddress();
  console.log(`Contrat déployé à : ${adresseContrat}`);
  // Sauvegarde de l'adresse pour les autres composants
  const config = {
    contractAddress: adresseContrat,
    deployedAt: new Date().toISOString(),
    network: "hardhat-local",
    deployer: deployeur.address,
  };
  fs.writeFileSync(
    path.join(__dirname, "../contract-config.json"),
    JSON.stringify(config, null, 2),
  );
  console.log("Configuration sauvegardée dans contract-config.json");
  // Test de sanité post-déploiement
  const nombreInitial = await contrat.nombreIdentites();
  console.log(`Nombre d'identités initial : ${nombreInitial} (attendu : 0)`);
}
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
