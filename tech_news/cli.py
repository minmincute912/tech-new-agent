"""Command line: python -m tech_news {run [--dry-run] | build}"""
import argparse

from .pipeline import run
from .site import build


def main():
    ap = argparse.ArgumentParser(prog="tech_news", description=__doc__)
    ap.add_argument("cmd", choices=["run", "build"])
    ap.add_argument("--dry-run", action="store_true", help="fetch and filter only; no AI, nothing written")
    args = ap.parse_args()
    run(args.dry_run) if args.cmd == "run" else build()
