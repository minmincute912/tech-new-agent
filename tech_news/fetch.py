"""Download and parse the RSS/Atom feeds."""
import calendar
import concurrent.futures as cf
import sys

import feedparser
import requests

from .config import UA


def fetch_feed(feed):
    r = requests.get(feed["url"], timeout=20, headers={"User-Agent": UA})
    r.raise_for_status()
    out = []
    for e in feedparser.parse(r.content).entries:
        ts = e.get("published_parsed") or e.get("updated_parsed")
        body = e.get("summary") or (e.get("content") or [{}])[0].get("value", "")
        out.append({"title": e.get("title", ""), "url": e.get("link", ""), "source": feed["name"],
                    "body": body, "published": calendar.timegm(ts) if ts else None})
    return out


def fetch_all(feeds):
    entries, failed = [], []
    with cf.ThreadPoolExecutor(8) as ex:
        for feed, fut in [(f, ex.submit(fetch_feed, f)) for f in feeds]:
            try:
                entries += fut.result()
            except Exception as err:  # noqa: BLE001 - one dead feed must not stop the run
                failed.append(feed["name"])
                print(f"  feed failed: {feed['name']}: {err}", file=sys.stderr)
    return entries, failed
