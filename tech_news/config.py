"""Paths and tunables shared by every module."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PUBLIC = ROOT / "public"
FEEDS_FILE = ROOT / "config" / "feeds.yaml"
REACH_FILE = ROOT / "config" / "reach.yaml"
PROMPT_FILE = ROOT / "config" / "classify-prompt.md"
SITE_TEMPLATE = ROOT / "web" / "index.html"
BRIEFS_FILE = DATA / "briefs.json"   # {"YYYY-MM-DD": {"text": ..., "n": ..., "sent": bool}}
SITE_URL = os.getenv("SITE_URL", "https://tech-news-1rf.pages.dev")

UA = "Mozilla/5.0 (compatible; tech-news-personal/1.0)"
BATCH = 8            # articles per AI call: keeps us inside free-tier rate limits and cuts tokens
GAP_SECONDS = 5      # pause between AI calls (free tier is ~15 requests/minute)
RETRY_WAIT = 10      # seconds before the second attempt on the same provider
SITE_DAYS = 30       # site shows the last 30 days (keeps data.json small); older rows stay in data/
CATEGORIES = {"ai-agents", "security", "cloud-infra", "fullstack", "opensource",
              "build-in-public", "hackathons", "general", "noise"}
