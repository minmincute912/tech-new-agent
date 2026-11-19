"""The daily run: fetch -> drop known -> filter -> classify in batches -> store."""
import sys
import time
from datetime import datetime, timezone

import yaml

from .config import BATCH, FEEDS_FILE, GAP_SECONDS, PROMPT_FILE
from .fetch import fetch_all
from .filters import select
from .llm import classify_batch, providers
from .reach import fetch_reach
from .store import append_rows, load_rows


def run(dry=False):
    feeds = yaml.safe_load(FEEDS_FILE.read_text("utf-8"))["feeds"]
    entries, failed = fetch_all(feeds)
    extra, _ = fetch_reach()
    entries += extra
    if not entries:
        sys.exit("no feed returned any entry")
    picked = select(entries, {r["url"] for r in load_rows(months=3)}, time.time())
    print(f"{len(entries)} entries from {len(feeds) - len(failed)}/{len(feeds)} feeds + {len(extra)} via agent-reach"
          f" -> {len(picked)} new to classify")
    if dry:
        for a in picked:
            print(f"  [{a['category']}] {a['source']}: {a['title'][:80]}")
        return
    provs = providers()
    if picked and not provs:
        sys.exit("no AI provider configured (set GEMINI_API_KEY and/or OPENROUTER_API_KEY)")
    system = PROMPT_FILE.read_text("utf-8")
    now_iso = datetime.now(timezone.utc).isoformat()
    ok = bad = 0
    for i in range(0, len(picked), BATCH):
        if i:
            time.sleep(GAP_SECONDS)
        rows = classify_batch(picked[i:i + BATCH], system, provs, now_iso)
        if rows is None:
            bad += 1
            continue
        append_rows(rows)
        ok += len(rows)
    print(f"stored {ok} articles, {bad} batches failed (retried next run)")
    if bad and not ok:
        sys.exit(1)
