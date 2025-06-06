from crewai_tools import SerperDevTool
import requests
import os

class FixedSerperTool(SerperDevTool):
    def _run(self, query: str, run_manager=None):
        print(f"🧪 Running FixedSerperTool on: {query}")

        try:
            # Use the same API key used by SerperDevTool internally
            api_key = os.getenv("SERPER_API_KEY")
            if not api_key:
                return "❌ SERPER_API_KEY is missing from environment"

            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json"
                },
                json={"q": query}
            )

            if response.status_code != 200:
                return f"❌ Serper API error {response.status_code}: {response.text}"

            json_data = response.json()
            results = json_data.get("organic", [])
            if not results:
                return f"ℹ️ No results for query: {query}"

            return [result.get("link") for result in results if result.get("link")]

        except Exception as e:
            return f"❌ Exception in FixedSerperTool: {e}"
