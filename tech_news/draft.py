"""Weekly build-in-public post ideas: top articles of the last 7 days -> AI -> private DM to the owner."""
import os
from datetime import datetime, timedelta, timezone

from .brief import send
from .config import DRAFT_PROMPT_FILE
from .llm import chat, providers
from .store import load_rows


def week_top(rows, now=None, n=10):
    cutoff = ((now or datetime.now(timezone.utc)) - timedelta(days=7)).isoformat()
    pool = {r["url"]: r for r in rows if r["category"] != "noise" and r["published_at"] >= cutoff and r["significance"] >= 3}
    newest = sorted(pool.values(), key=lambda r: r["published_at"], reverse=True)
    return sorted(newest, key=lambda r: -r["significance"])[:n]  # stable: newest first inside a score


def draft(rows=None, call=chat, send_fn=send, provs=None):
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_ALERT_CHAT_ID")
    if not (token and chat_id):
        print("alert chat not configured, skipping draft")
        return
    top = week_top(rows if rows is not None else load_rows(months=2))
    if len(top) < 3:
        print("not enough articles for a draft")
        return
    system = DRAFT_PROMPT_FILE.read_text("utf-8")
    user = "\n".join(f"[{i}] {r['kind'] if 'kind' in r else 'news'} | {r['title']}: {r['summary']} {r.get('action', '')} ({r['url']})"
                     for i, r in enumerate(top, 1))
    for p in provs if provs is not None else providers():
        try:
            text = (call(p, system, user) or "").strip()
            if text:
                send_fn("✍️ Ý tưởng bài build in public tuần này\n\n" + text[:3900], token, chat_id, None)
                print("draft sent")
                return
        except Exception as err:  # noqa: BLE001 - try the next provider
            print(f"  draft via {p['name']} failed: {err}")
    raise SystemExit("draft failed on every provider")
