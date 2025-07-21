# 🚀 wallet_routes.py - Handles wallet verification from GameChanger

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

router = APIRouter()

# ✅ DRMZ Pool ID (as confirmed)
DRMZ_POOL_ID = "d71613e6097382e4d522fb17cff10b6c8bbe8575521ae174ba506c70"

# 📦 Pydantic model for incoming data
class WalletVerificationPayload(BaseModel):
    address: str
    stakeKey: str
    delegatedPool: str

# 🎯 POST route to verify wallet
@router.post("/api/wallet/verify")
async def verify_wallet(payload: WalletVerificationPayload):
    try:
        logging.info(f"🔍 Verifying wallet: {payload.address} (Stake: {payload.stakeKey})")

        if payload.delegatedPool == DRMZ_POOL_ID:
            tier = "Delegated"
            logging.info("✅ Delegation to DRMZ confirmed.")
        else:
            tier = "Free"
            logging.info("⚠️ Wallet is NOT delegated to DRMZ.")

        # Return result
        return JSONResponse(
            content={
                "success": True,
                "wallet": payload.address,
                "stakeKey": payload.stakeKey,
                "tier": tier
            },
            status_code=200
        )

    except Exception as e:
        logging.error(f"❌ Wallet verification error: {str(e)}")
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )
