const hre = require("hardhat");

async function main() {
  const contractAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
  const IdentityRegistry = await hre.ethers.getContractFactory(
    "IdentityRegistry",
  );
  const contract = IdentityRegistry.attach(contractAddress);
  const address = "0x742d35cc6634c0532925a3b8d4c9c8f3";
  const did = "did:ethr:" + address;
  const hash =
    "0x0000000000000000000000000000000000000000000000000000000000000000";
  const tx = await contract.enregistrer(address, did, hash);
  await tx.wait();
  console.log("Adresse enregistrée");
}

main().catch(console.error);
