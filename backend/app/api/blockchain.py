from fastapi import APIRouter, Depends, HTTPException
from web3 import Web3
from app.services.blockchain_simulator import get_contract
from app.core.security import get_current_user

router = APIRouter(prefix="/blockchain", tags=["blockchain"])

@router.get("/verify/{address}")
async def verify_identity(address: str):
    if not Web3.is_address(address):
        raise HTTPException(status_code=400, detail="Adresse invalide")
    contract = get_contract()
    is_active = contract.functions.verifier(address).call()
    return {"address": address, "active": is_active}

@router.post("/revoke", dependencies=[Depends(get_current_user)])
async def revoke_identity(request: dict):
    address = request.get("address") or request.get("did", "").replace("did:ethr:", "")
    if not Web3.is_address(address):
        raise HTTPException(status_code=400, detail="Adresse invalide")
    contract = get_contract()
    w3 = contract.w3
    tx = contract.functions.revoquer(address).transact({'from': w3.eth.accounts[0]})
    receipt = w3.eth.wait_for_transaction_receipt(tx)
    if receipt.status != 1:
        raise HTTPException(status_code=500, detail="Échec")
    return {"message": "Révoquée", "tx_hash": receipt.transactionHash.hex()}