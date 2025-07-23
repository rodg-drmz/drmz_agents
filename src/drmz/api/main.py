# src/drmz/api/main.py

from dotenv import load_dotenv
load_dotenv() # <-- Load environment variables from .env file

from fastapi import FastAPI
from drmz.api.crew_gateway import app as crew_app
from drmz.api.drmz_dapp_api import app as dapp_app

app = FastAPI(
    title="Morpheus API Gateway",
    description="Unified API for Morpheus Agents, DRMZ flows, and frontend chat tools.",
    version="1.0.0"
)

# Mount the CrewAI agent routes under /crew/
app.mount("/crew", crew_app)

# Mount the DRMZ wallet + flows API under /dapp/
app.mount("/dapp", dapp_app)

@app.get("/")
def root():
    return {"message": "🌐 Morpheus API is online. Visit /crew/agents/list or /dapp for routes."}
