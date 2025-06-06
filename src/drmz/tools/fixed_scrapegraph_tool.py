# src/drmz/tools/fixed_scrapegraph_tool.py

from crewai_tools import ScrapegraphScrapeTool

class FixedScrapegraphTool(ScrapegraphScrapeTool):
    def _run(self, query: dict, run_manager=None):
        print(f"🧪 Running FixedScrapegraphTool on: {query.get('url')}")
        try:
            # Call the underlying logic manually (if it's .scrape or .run or similar)
            return self.run(query)
        except Exception as e:
            return f"🔴 Scraping failed: {e}"
