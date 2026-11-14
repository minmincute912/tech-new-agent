"""Paths and tunables shared by every module."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PUBLIC = ROOT / "public"
FEEDS_FILE = ROOT / "config" / "feeds.yaml"
REACH_FILE = ROOT / "config" / "reach.yaml"
PROMPT_FILE = ROOT / "config" / "classify-prompt.md"
SITE_TEMPLATE = ROOT / "web" / "index.html"

UA = "Mozilla/5.0 (compatible; tech-news-personal/1.0)"
BATCH = 8            # articles per AI call: keeps us inside free-tier rate limits and cuts tokens
GAP_SECONDS = 5      # pause between AI calls (free tier is ~15 requests/minute)
RETRY_WAIT = 10      # seconds before the second attempt on the same provider
SITE_DAYS = 90       # shortcut: site shows the last 90 days only, older rows stay in data/
CATEGORIES = {"ai-agents", "security", "cloud-infra", "fullstack", "opensource",
              "build-in-public", "hackathons", "general", "noise"}
