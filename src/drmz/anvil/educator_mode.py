# Educator Mode
from .anvil_config import call_anvil_api

def explain_contract(contract_id: str):
    """Get and explain a contract by ID."""
    data = call_anvil_api(f"contracts/{contract_id}")
    if not data:
        return "❌ Failed to retrieve contract data."
    
    # Here you would process and explain it in plain English (Morpheus style)
    name = data.get("name", "Unnamed")
    actions = data.get("actions", [])
    
    summary = f"🧠 **Contract Name:** {name}\n"
    summary += f"🔍 This contract supports {len(actions)} action(s):\n"
    for action in actions:
        summary += f"• `{action['name']}` – {action.get('description', 'No description')}\n"
    
    return summary

def demo_mint():
    """Run a sample mint simulation via Ada Anvil."""
    payload = {
        "name": "Test NFT",
        "description": "Minted by Morpheus on Anvil testnet.",
        "policy": {"type": "random"},
        "metadata": {"type": "CIP-25"}
    }
    result = call_anvil_api("simulate/mint", method="POST", payload=payload)
    if not result:
        return "❌ Simulation failed."
    
    tx = result.get("transaction", {})
    return f"✅ Simulated mint! TX Hash: {tx.get('hash', 'N/A')}"
