import json
import re
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from crewai.flow import Flow, start

from drmz_crewai.crews.morpheus_crew import MorpheusCrew

# ── Data Models ────────────────────────────────────────────────────────────────
Stage = Literal[
    "chat", "intro", "confirmName", "walletIntro", 
    "secureKeywords", "awaitingWallet", "stakingEducation", 
    "governanceEducation", "complete"
]

class UserData(BaseModel):
    name: Optional[str] = None
    wallet_address: Optional[str] = None
    stage: Stage = "chat"
    onboarding_started: bool = False

class ChatState(BaseModel):
    message: str = ""
    user_data: UserData = Field(default_factory=UserData)
    history: list = Field(default_factory=list)
    response: str = ""
    captured_data: Dict[str, Any] = Field(default_factory=dict)

# ── Hardcoded Onboarding Logic ─────────────────────────────────────────────────
class OnboardingLogic:
    """Hardcoded onboarding flow logic - no AI needed for state management."""
    
    def __init__(self):
        self.name_pattern = re.compile(r"^[a-zA-Z0-9_-]{2,}$")
        self.addr_pattern = re.compile(r"addr1[0-9a-z]{20,}", re.I)
    
    def process_onboarding_message(self, message: str, user_data: UserData) -> tuple[str, UserData, Dict[str, Any]]:
        """Process onboarding message and return (response, updated_user_data, captured_data)."""
        
        m = message.strip()
        captured = {}
        
        if user_data.stage == "intro":
            if self.name_pattern.fullmatch(m):
                user_data.name = m
                user_data.stage = "confirmName"
                captured["name"] = m
                return (
                    f"Excellent, {m}! A name worthy of the blockchain. 💫\n\n"
                    f"Shall I call you {m} throughout our journey? (Yes/No)",
                    user_data,
                    captured
                )
            else:
                return (
                    f'"{m}" doesn\'t quite fit the pattern of a blockchain identity. 🔗\n\n'
                    "Try a name with letters, numbers, underscores, or hyphens (at least 2 characters).",
                    user_data,
                    {}
                )
        
        elif user_data.stage == "confirmName":
            if m.lower() in ["yes", "y", "yeah", "yep"]:
                user_data.stage = "walletIntro"
                return (
                    f"Perfect, {user_data.name}! Let's begin your Cardano education. 🎓\n\n"
                    "To participate in the Cardano ecosystem, you'll need a wallet. I recommend:\n\n"
                    "🔹 **Eternl** - Feature-rich, great for advanced users\n"
                    "🔹 **Lace** - Official IOG wallet, clean interface\n"
                    "🔹 **VESPR** - Mobile-focused, user-friendly\n"
                    "🔹 **GameChanger** - Powerful scripting capabilities\n\n"
                    "Download one from their official website. When ready, type **Done**.",
                    user_data,
                    {}
                )
            else:
                user_data.stage = "intro"
                user_data.name = None
                return ("No worries! What name would you prefer instead?", user_data, {})
        
        elif user_data.stage == "walletIntro":
            if m.lower() in ["done", "ready", "finished"]:
                user_data.stage = "secureKeywords"
                return (
                    "Excellent! 🎉 Now comes the most important part - your **seed phrase**.\n\n"
                    "⚠️  **CRITICAL SECURITY LESSON:**\n"
                    "• Your seed phrase = complete wallet control\n"
                    "• Write it down on paper (never digital)\n"
                    "• Store in a safe place\n"
                    "• NEVER share with anyone\n"
                    "• No legitimate service will ask for it\n\n"
                    "Create your wallet and secure your seed phrase. Reply **Secured** when done.",
                    user_data,
                    {}
                )
            else:
                return ("Take your time setting up the wallet. Type **Done** when it's installed.", user_data, {})
        
        elif user_data.stage == "secureKeywords":
            if m.lower() in ["secured", "secure", "done"]:
                user_data.stage = "awaitingWallet"
                return (
                    "🛡️ Well done! Security first is the Cardano way.\n\n"
                    "Now I need your wallet's **receive address** to verify everything is working. "
                    "In your wallet, look for 'Receive' or 'Address' - it starts with `addr1...`\n\n"
                    "Paste it here (this is safe to share - it's like your email address for ADA).",
                    user_data,
                    {}
                )
            else:
                return ('Please reply **Secured** once you\'ve safely stored your seed phrase offline.', user_data, {})
        
        elif user_data.stage == "awaitingWallet":
            if self.addr_pattern.search(m):
                user_data.wallet_address = m.strip()
                user_data.stage = "stakingEducation"
                captured["wallet_address"] = m.strip()
                return (
                    "✅ Perfect! Your wallet is ready.\n\n"
                    f"**Next: Understanding Staking**\n\n"
                    "Staking your ADA helps secure the Cardano network and earns you rewards (typically 4-6% annually). "
                    "You delegate to a stake pool operator who runs the infrastructure. Your ADA never leaves your wallet.\n\n"
                    "🏛️ **DRMZ Pool Benefits:**\n"
                    "• Supports blockchain education\n"
                    "• Community-focused mission\n"
                    "• Reliable performance\n"
                    "• Educational resources\n\n"
                    "Ready to learn how to stake with DRMZ? Type **Staking**.",
                    user_data,
                    captured
                )
            else:
                return (
                    "That doesn't look like a Cardano address. 🤔\n\n"
                    "Look for an address starting with `addr1...` in your wallet's receive section.",
                    user_data,
                    {}
                )
        
        elif user_data.stage == "stakingEducation":
            if m.lower() in ["staking", "stake", "ready"]:
                user_data.stage = "governanceEducation"
                return (
                    f"Excellent, {user_data.name}! Here's how to stake with DRMZ:\n\n"
                    "**Steps:**\n"
                    "1️⃣ Open your wallet\n"
                    "2️⃣ Find 'Staking' or 'Delegation'\n"
                    "3️⃣ Search for **DRMZ**\n"
                    "4️⃣ Delegate your ADA\n\n"
                    "🗳️ **Next: Understanding Cardano Governance**\n\n"
                    "Cardano's governance system lets ADA holders vote on protocol changes and funding proposals. "
                    "You can delegate your voting power to a DRep (Delegated Representative) or become one yourself.\n\n"
                    "Want to learn about DReps? Type **Governance**.",
                    user_data,
                    {}
                )
            else:
                return ('Type **Staking** to learn about delegation.', user_data, {})
        
        elif user_data.stage == "governanceEducation":
            if m.lower() in ["governance", "dreps", "drep", "ready"]:
                user_data.stage = "complete"
                return (
                    f"🌟 **Congratulations, {user_data.name}!** 🎉\n\n"
                    "You've successfully:\n"
                    "✅ Set up a Cardano wallet\n"
                    "✅ Learned about security\n"
                    "✅ Understood staking\n"
                    "✅ Explored governance\n\n"
                    "**About DReps:**\n"
                    "DReps are elected representatives who vote on your behalf in Cardano governance. "
                    "They research proposals and represent their delegators' interests. You can:\n"
                    "• Delegate to an existing DRep\n"
                    "• Become a DRep yourself (requires 500 ADA deposit)\n"
                    "• Vote directly on proposals\n\n"
                    "You're now a true Cardano citizen! Welcome to the DRMZ community. 💜\n\n"
                    "Feel free to ask me anything about Cardano anytime!",
                    user_data,
                    {}
                )
            else:
                return ('Type **Governance** to learn about DReps and voting.', user_data, {})
        
        # Fallback
        return ("I'm not sure how to respond in this context. Please follow the suggested prompts.", user_data, {})

# ── Simplified Flow ────────────────────────────────────────────────────────────
class MorpheusChatFlow(Flow[ChatState]):
    """Morpheus chat flow with hardcoded onboarding logic."""

    def __init__(self):
        super().__init__()
        self.morpheus_crew = MorpheusCrew()
        self.onboarding = OnboardingLogic()

    @start()
    def process_message(self):
        """Single method that handles routing and execution."""
        
        # Check if user is initiating onboarding
        if self.state.message.lower().startswith("drmz initiate"):
            self.state.user_data.onboarding_started = True
            self.state.user_data.stage = "intro"
            self.state.response = (
                "🌌 Greetings, seeker of knowledge. I am Morpheus, your guide through the Cardano realm.\n\n"
                "I'll help you understand this revolutionary blockchain while setting up your first wallet. "
                "This journey will teach you about wallets, staking, and governance.\n\n"
                "What shall I call you on this adventure?"
            )
            return self.state.response
        
        # Check if user is in active onboarding flow
        elif self.state.user_data.onboarding_started and self.state.user_data.stage != "complete":
            return self._handle_onboarding()
        
        # Default to chat
        else:
            return self._handle_chat()

    def _handle_chat(self):
        """Handle general chat with Morpheus using CrewAI."""
        
        result = self.morpheus_crew.crew("chat").kickoff(inputs={
            "message": self.state.message,
            "stage": self.state.user_data.stage,
            "username": self.state.user_data.name,
            "history": self.state.history[-5:] if self.state.history else []
        })
        
        self.state.response = result.raw if hasattr(result, 'raw') else str(result)
        
        # Add to conversation history
        self.state.history.append({
            "user": self.state.message,
            "morpheus": self.state.response,
            "timestamp": self._get_timestamp()
        })
        
        return self.state.response

    def _handle_onboarding(self):
        """Handle onboarding flow using hardcoded logic."""
        
        # Use hardcoded logic instead of AI
        response, updated_user_data, captured = self.onboarding.process_onboarding_message(
            self.state.message, 
            self.state.user_data
        )
        
        # Update state
        self.state.response = response
        self.state.user_data = updated_user_data
        
        # Capture user data
        if captured:
            self.state.captured_data.update(captured)
        
        # Mark onboarding complete and return to chat mode
        if self.state.user_data.stage == "complete":
            self.state.user_data.onboarding_started = False
            self.state.user_data.stage = "chat"
            self._save_user_data()
        
        # Add to conversation history
        self.state.history.append({
            "user": self.state.message,
            "morpheus": self.state.response,
            "stage": self.state.user_data.stage,
            "timestamp": self._get_timestamp()
        })
        
        return self.state.response

    def _save_user_data(self):
        """Save captured user data."""
        if self.state.captured_data:
            print(f"🎉 New user onboarded: {self.state.captured_data}")
            
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()

# ── Persistent CLI Session ────────────────────────────────────────────────────
def kickoff():
    """Interactive CLI that maintains state across messages."""
    print("🌌 Morpheus Chat Flow - Type 'exit' to quit")
    print("Try 'drmz initiate' to start onboarding!")
    
    # Create ONE flow instance that persists
    flow = MorpheusChatFlow()
    
    while True:
        message = input("\n👤 You: ")
        if message.lower() == 'exit':
            break
            
        # Set message and run flow
        flow.state.message = message
        response = flow.kickoff()
        
        print(f"🧙‍♂️ Morpheus: {response}")
        
        # Show captured data when onboarding completes
        if flow.state.captured_data and not flow.state.user_data.onboarding_started:
            print(f"\n🎉 Onboarding complete! Captured: {flow.state.captured_data}")

if __name__ == "__main__":
    kickoff()

# Add this at the end of your morpheus_chat_flow.py file
# ── Enterprise Deployment Entry Point ──────────────────────────────────────────
def chat_endpoint(message: str, user_data: dict = None) -> dict:
    """
    Enterprise deployment endpoint.
    Returns structured response for API consumption.
    """
    flow = MorpheusChatFlow()
    
    # Load user data if provided
    if user_data:
        flow.state.user_data = UserData(**user_data)
        flow.state.history = user_data.get("history", [])
    
    # Set message and execute
    flow.state.message = message
    response = flow.kickoff()
    
    return {
        "response": response,
        "user_data": {
            "name": flow.state.user_data.name,
            "wallet_address": flow.state.user_data.wallet_address,
            "stage": flow.state.user_data.stage,
            "onboarding_active": flow.state.user_data.onboarding_started,
            "captured_data": flow.state.captured_data,
            "history": flow.state.history
        },
        "onboarding_complete": (
            flow.state.user_data.stage == "chat" and 
            bool(flow.state.captured_data)
        )
    }

# Export for enterprise deployment
__all__ = ["MorpheusChatFlow", "chat_endpoint", "kickoff"]