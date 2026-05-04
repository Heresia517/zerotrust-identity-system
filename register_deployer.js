const { ethers } = require("ethers");

async function main() {
    const provider = new ethers.JsonRpcProvider("http://localhost:8545");
    const signer = await provider.getSigner(0);
    const contractAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
    const abi = [
        "function enregistrer(address utilisateur, string did, bytes32 hashDonnees) external",
        "function verifier(address utilisateur) external view returns (bool)"
    ];
    const contract = new ethers.Contract(contractAddress, abi, signer);
    const address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266";
    const did = "did:ethr:" + address;
    const hash = "0x0000000000000000000000000000000000000000000000000000000000000000";
    const tx = await contract.enregistrer(address, did, hash);
    await tx.wait();
    console.log("Adresse enregistrée");
}

main().catch(console.error);
