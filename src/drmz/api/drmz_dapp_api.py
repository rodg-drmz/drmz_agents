# src/drmz/api/drmz_dapp_api.py

from fastapi import FastAPI
from drmz.routes import wallet_routes

app = FastAPI(
    title="DRMZ DApp API",
    description="Backend for drmz-dapp, including wallet verification and Morpheus flows.",
    version="1.0"
)

# 🔌 Include GameChanger wallet route (more routes can be added)
app.include_router(wallet_routes.router)

@app.get("/")
def root():
    return {"message": "DRMZ DApp API is running. Morpheus is listening."}
