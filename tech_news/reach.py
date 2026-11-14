"""Extra sources through the Agent-Reach CLI (GitHub / YouTube / web search); same entry shape as fetch.py."""
import json
import shlex
import shutil
import subprocess
import sys
from datetime import datetime

import yaml

from .config import REACH_FILE


def parse_items(out, source, undated=False):
    """Agent-Reach JSON -> pipeline entries. `ok: false` or bad JSON raises, so the caller skips that command."""
    data = json.loads(out)
    if not data.get("ok"):
        raise RuntimeError((data.get("error") or {}).get("message", "agent-reach failed"))
    entries = []
    for i in data.get("items", []):
        ts = None if undated else i.get("published_at")  # GitHub gives the repo creation date, not news age
        entries.append({"title": i.get("title", ""), "url": i.get("url", ""), "source": source,
                        "body": i.get("text") or "",
                        "published": datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() if ts else None})
    return entries


def fetch_reach():
    jobs = yaml.safe_load(REACH_FILE.read_text("utf-8")) if REACH_FILE.exists() else []
    if not jobs:
        return [], []
    exe = shutil.which("agent-reach")
    if not exe:
        print("  agent-reach not installed, skipping extra sources", file=sys.stderr)
        return [], [j["source"] for j in jobs]
    entries, failed = [], []
    for j in jobs:
        try:
            r = subprocess.run([exe, *shlex.split(j["cmd"])], capture_output=True, text=True, timeout=90, check=False)
            entries += parse_items(r.stdout, j["source"], j.get("undated", False))
        except Exception as err:  # noqa: BLE001 - one broken command must not stop the run
            failed.append(j["source"])
            print(f"  reach failed: {j['source']}: {err}", file=sys.stderr)
    return entries, failed
