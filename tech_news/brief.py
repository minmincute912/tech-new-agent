"""Telegram digest of the day's top articles; briefs.json only remembers which days were sent."""
import html
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from .config import BRIEFS_FILE, SITE_URL
from .store import load_rows

VN = timezone(timedelta(hours=7))
LIGHT = {"opensource", "build-in-public"}  # weekly-only on the site, so kept out of the daily brief and digest


def vn_day(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(VN).strftime("%Y-%m-%d")


def today_vn():
    return datetime.now(VN).strftime("%Y-%m-%d")


def load_briefs(path: Path = BRIEFS_FILE):
    return json.loads(path.read_text("utf-8")) if path.exists() else {}


def save_briefs(briefs, path: Path = BRIEFS_FILE):
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(briefs, ensure_ascii=False, indent=1, sort_keys=True), "utf-8")


def top_of_day(rows, day, n=10, per_cat=2):
    """Most important articles published on `day`, at most `per_cat` per category, light categories excluded."""
    pool = [r for r in {r["url"]: r for r in rows}.values()
            if r["category"] != "noise" and r["category"] not in LIGHT and vn_day(r["published_at"]) == day]
    pool.sort(key=lambda r: r["published_at"], reverse=True)
    pool.sort(key=lambda r: -r["significance"])  # stable: newest first inside the same score
    out, per = [], {}
    for r in pool:
        if len(out) < n and per.get(r["category"], 0) < per_cat:
            out.append(r)
            per[r["category"]] = per.get(r["category"], 0) + 1
    return out


def format_message(day, top, site_url=SITE_URL, limit=4000):
    """Telegram HTML message; article lines are dropped from the end if it would exceed the 4096 limit."""
    head = f"📰 <b>Tech News · {day[8:]}/{day[5:7]}</b>\n"
    foot = f'\n👉 <a href="{html.escape(site_url, quote=True)}">Xem tất cả tin</a>'
    lines = [f'{i}. <a href="{html.escape(r["url"], quote=True)}">{html.escape(r["title"])}</a> '
             f'<i>({html.escape(r["source"])})</i>'
             + (f'\n   → {html.escape(r["action"])}' if r.get("action") else "") for i, r in enumerate(top, 1)]
    while lines and len(head) + len("\n★ Nổi bật\n" + "\n".join(lines)) + len(foot) > limit:
        lines.pop()
    return head + ("\n★ Nổi bật\n" + "\n".join(lines) + "\n" if lines else "") + foot


def send(text, token, chat_id, parse_mode="HTML"):
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=30,
                      json={"chat_id": chat_id, "text": text, **({"parse_mode": parse_mode} if parse_mode else {}),
                            "disable_web_page_preview": True})
    r.raise_for_status()


def notify(send_fn=send, rows=None, day=None):
    """Send today's digest once. Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (for a channel: @channelname)."""
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (token and chat_id):
        print("telegram not configured, skipping")
        return
    day = day or today_vn()
    briefs = load_briefs()
    if briefs.get(day, {}).get("sent"):
        print(f"digest for {day} already sent")
        return
    top = top_of_day(rows if rows is not None else load_rows(months=1), day, 5)
    if not top:
        print(f"nothing to send for {day}")
        return
    send_fn(format_message(day, top), token, chat_id)
    briefs.setdefault(day, {})["sent"] = True
    save_briefs(briefs)
    print(f"digest for {day} sent")
