"""Build the static site: public/index.html + public/data.json (noise hidden, last SITE_DAYS days)."""
import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .brief import load_briefs
from .config import DATA, PUBLIC, SITE_DAYS, SITE_TEMPLATE
from .store import load_rows


def build(data_dir: Path = DATA, out_dir: Path = PUBLIC):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=SITE_DAYS)).isoformat()
    rows = {r["url"]: r for r in load_rows(data_dir) if r["category"] != "noise" and r["published_at"] >= cutoff}
    arts = sorted(rows.values(), key=lambda r: r["published_at"], reverse=True)
    out_dir.mkdir(exist_ok=True)
    shutil.copy(SITE_TEMPLATE, out_dir / "index.html")
    day0 = cutoff[:10]
    briefs = {d: {"text": v["text"]} for d, v in load_briefs(data_dir / "briefs.json").items() if v.get("text") and d >= day0}
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    telegram = f"https://t.me/{chat[1:]}" if chat.startswith("@") else os.getenv("TELEGRAM_CHANNEL_URL", "")
    (out_dir / "data.json").write_text(json.dumps(
        {"generated": datetime.now(timezone.utc).isoformat(), "articles": arts, "briefs": briefs, "telegram": telegram},
        ensure_ascii=False), "utf-8")
    print(f"built {out_dir.name}/ with {len(arts)} articles")
