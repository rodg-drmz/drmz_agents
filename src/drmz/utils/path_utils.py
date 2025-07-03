from pathlib import Path

# Start from: src/drmz/utils/ → go up two levels
PROJECT_ROOT = Path(__file__).parents[2]

CONFIG_DIR = PROJECT_ROOT / "config"
KNOWLEDGE_DIR = PROJECT_ROOT.parent / "knowledge"
ARCHIVE_DIR = KNOWLEDGE_DIR / "archive"
PERMANENT_DIR = KNOWLEDGE_DIR / "permanent"

OUTPUT_DIR = PROJECT_ROOT.parent / "output"
GUIDES_DIR = OUTPUT_DIR / "guides"
CURRICULUM_DIR = OUTPUT_DIR / "curriculum"
ONBOARDING_DIR = OUTPUT_DIR / "onboarding"
LOGS_DIR = OUTPUT_DIR / "logs"
