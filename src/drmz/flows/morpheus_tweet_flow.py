from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add 'src' to the path for relative imports
sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from crewai.flow.flow import Flow, start, listen
from drmz.tools.fixed_scrapegraph_tool import FixedScrapegraphTool
from drmz.crews.morpheus_crew import MorpheusCrew
from src.drmz.crews.config_loader import load_agents, load_tasks
from drmz.tools.fixed_serper_tool import FixedSerperTool  # 👈 Replaces default SerperDevTool

# ───────────────────────────────────────────────────────────────
# 🔧 Load environment variables
# ───────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
api_key = os.getenv("DRMZ_SGAI_API_KEY")
print("🔍 Loaded SGAI_API_KEEY:", api_key if api_key else "❌ Not Found")

# 🔑 Search terms of interest
PRIORITY_TERMS = ["DRMZ", "ADA staking", "Bitcoin", "Cardano", "DeFi", "zk", "zero knowledge", "RWA"]

# ───────────────────────────────────────────────────────────────
# 🧠 Auto Tone Detection Logic
# ───────────────────────────────────────────────────────────────
def determine_tone_from_topic(content: str) -> str:
    """Infer tone variant based on keywords in the content."""
    content_lower = content.lower()

    educator_keywords = ["how to", "explained", "beginner", "what is", "guide", "tutorial", "walkthrough"]
    dreamer_keywords = ["future", "vision", "dream", "reimagine", "possibility", "hope", "potential"]
    provocateur_keywords = ["why", "broken", "flawed", "problem", "needs fixing", "challenge", "debate"]

    if any(word in content_lower for word in educator_keywords):
        return "educator"
    elif any(word in content_lower for word in dreamer_keywords):
        return "dreamer"
    elif any(word in content_lower for word in provocateur_keywords):
        return "provocateur"
    else:
        print("⚠️ Tone detection uncertain — defaulting to educator.")
        return "educator"  # default fallback

# ───────────────────────────────────────────────────────────────
# 🚀 Morpheus Tweet Flow Class
# ───────────────────────────────────────────────────────────────
class MorpheusTweetFlow(Flow[str]):
    def __init__(self):
        super().__init__()
        self.agents = load_agents()
        self.tasks = load_tasks()
        self.morpheus = MorpheusCrew(self.agents, self.tasks)
        self.web_search = FixedSerperTool()
        self.scraper = FixedScrapegraphTool(api_key=api_key)

        print(f"🛠️ Using tool class: {self.web_search.__class__.__name__}")

    @start()
    def gather_sources(self):
        """🔍 Perform web searches for trending content"""
        print("🔍 Searching for trending news and discussions...")

        queries = [
            f"latest news on {term} site:twitter.com" for term in PRIORITY_TERMS
        ] + [
            f"trending discussions about {term} site:reddit.com" for term in PRIORITY_TERMS
        ]

        results = []
        for q in queries:
            try:
                response = self.web_search._run(q, run_manager=None)
                if isinstance(response, list):
                    results.extend(response[:2])
            except Exception as e:
                print(f"❌ Search error for '{q}': {e}")

        print(f"✅ Retrieved {len(results)} links")
        self.state["results"] = results
        return results

    @listen(gather_sources)
    def generate_tweet(self, links):
        """🧠 Scrape content and generate tweet via Morpheus"""
        print("🧠 Scraping pages and preparing tweet content...")
        all_texts = []

        for link in links:
            try:
                page_text = self.scraper.run({"url": link})
                if page_text:
                    all_texts.append(page_text)
            except Exception as e:
                print(f"⚠️ Scraping failed for {link}: {e}")

        if not all_texts:
            print("⚠️ No content to summarize — skipping tweet generation.")
            return "No relevant content found."

        combined_content = "\n\n".join(all_texts[:6])
        tone = determine_tone_from_topic(combined_content)
        print(f"🧭 Detected tone: {tone}")

        task_map = {
            "educator": "morpheus_tweet_task_educator",
            "dreamer": "morpheus_tweet_task_dreamer",
            "provocateur": "morpheus_tweet_task_provocateur"
        }
        selected_task = task_map.get(tone, "morpheus_tweet_task_educator")

        result = self.morpheus.tweet_crew(task_name=selected_task).kickoff(inputs={"topic": combined_content})
        tweet = getattr(result, "output", None) or getattr(result, "raw", "No tweet generated.")

        # 🔍 Add this to inspect the raw tweet before cleanup
        print("\n=== 📝 Pre-Cleanup Tweet ===\n")
        print(tweet.strip())

        cleaned_result = self.morpheus.get_editor_crew().kickoff(inputs={"topic": tweet})
        final_tweet = getattr(cleaned_result, "output", None) or getattr(cleaned_result, "raw", tweet)

        print("\n=== 📣 Suggested Tweet ===\n")
        print(final_tweet.strip())

        os.makedirs("output/tweets", exist_ok=True)
        with open("output/tweets/generated_tweet.txt", "w", encoding="utf-8") as f:
            f.write(final_tweet.strip())

        return final_tweet

# ───────────────────────────────────────────────────────────────
# 🏁 Main Execution
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MorpheusTweetFlow().kickoff()
    print("\n=== ✅ Tweet Flow Complete ===")
