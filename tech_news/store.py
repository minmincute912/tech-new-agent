"""Append-only storage: one JSON object per line, one file per month."""
import json
from pathlib import Path

from .config import DATA


def load_rows(data_dir: Path = DATA):
    return [json.loads(line) for f in sorted(data_dir.glob("*.jsonl"))
            for line in f.read_text("utf-8").splitlines() if line]


def append_rows(rows, data_dir: Path = DATA):
    data_dir.mkdir(exist_ok=True)
    for r in rows:
        with open(data_dir / f"{r['processed_at'][:7]}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
