from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
assert w3.is_connected(), "Hardhat non joignable"

contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "utilisateur", "type": "address"},
            {"internalType": "string", "name": "did", "type": "string"},
            {"internalType": "bytes32", "name": "hashDonnees", "type": "bytes32"}
        ],
        "name": "enregistrer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = w3.eth.contract(address=contract_address, abi=abi)

address_to_register = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
did = "did:ethr:" + address_to_register
hash_vide = "0x" + "0" * 64

admin = w3.eth.accounts[0]
tx = contract.functions.enregistrer(address_to_register, did, hash_vide).transact({'from': admin})
receipt = w3.eth.wait_for_transaction_receipt(tx)
print(f"Transaction hash: {receipt.transactionHash.hex()}")
print(f"Status: {receipt.status} (1 = succès)")
if receipt.status == 1:
    print("✅ Adresse enregistrée avec succès !")
else:
    print("❌ Échec de l'enregistrement")