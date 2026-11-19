"""AI classification: OpenAI-compatible providers tried in order, with validation of the reply."""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

from .config import CATEGORIES, RETRY_WAIT


def providers():
    """Primary first, fallbacks after. A provider without a key is skipped."""
    cfg = [
        ("gemini", "https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY",
         os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")),
        ("openrouter", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY",
         os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")),
        ("kyma", "https://kymaapi.com/v1", "KYMA_API_KEY", os.getenv("KYMA_MODEL", "")),
    ]
    return [{"name": n, "base": b, "key": os.environ[k], "model": m}
            for n, b, k, m in cfg if os.getenv(k) and m]


def chat(p, system, user):
    r = requests.post(f"{p['base']}/chat/completions", timeout=90,
                      headers={"Authorization": f"Bearer {p['key']}"},
                      json={"model": p["model"], "temperature": 0.2, "max_tokens": 4096,
                            "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": user}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def make_prompt(batch):
    return "\n\n".join(f"[{i}] Title: {a['title']}\nSource: {a['source']}\nSnippet: {a['description'][:300]}"
                       for i, a in enumerate(batch, 1))


def parse_ai(text, batch, now_iso):
    """Rows for the articles the model answered validly; the rest are left for the next run."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE)
    arr = json.loads(text[text.index("["): text.rindex("]") + 1])
    by_id = {p.get("id"): p for p in arr if isinstance(p, dict)}
    rows = []
    for i, a in enumerate(batch, 1):
        p = by_id.get(i)
        if not p:
            continue
        summary = str(p.get("summary", "")).strip()
        sig = p.get("significance")
        if not summary or not isinstance(sig, int) or isinstance(sig, bool) or not 1 <= sig <= 5:
            continue
        cat = a["category"] if a["forced"] or p.get("category") not in CATEGORIES else p["category"]
        rows.append({"title": str(p.get("vietnamese_title") or a["title"]).strip(), "summary": summary,
                     "url": a["url"], "source": a["source"], "category": cat, "significance": sig,
                     "published_at": datetime.fromtimestamp(a["published"], timezone.utc).isoformat(),
                     "processed_at": now_iso, "requires_review": sig >= 5})
    if not rows:
        raise ValueError("no valid rows in AI response")
    return rows


def classify_batch(batch, system, provs, now_iso, call=chat, wait=RETRY_WAIT):
    """Try each provider twice in order; None means every provider failed (batch is retried next run)."""
    for p in provs:
        for attempt in range(2):
            try:
                return parse_ai(call(p, system, make_prompt(batch)), batch, now_iso)
            except Exception as err:  # noqa: BLE001 - any provider failure means try the next one
                print(f"  {p['name']} attempt {attempt + 1} failed: {err}", file=sys.stderr)
                if attempt == 0:
                    time.sleep(wait)
    return None
