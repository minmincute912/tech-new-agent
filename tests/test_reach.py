import json

import pytest

from tech_news.filters import select
from tech_news.reach import parse_items

OK = json.dumps({"ok": True, "items": [
    {"title": "Hackathon AI Hà Nội 2026", "url": "https://x.vn/a", "text": "cuộc thi hackathon", "published_at": "2026-11-13T00:00:00Z"},
    {"title": "Video no date", "url": "https://y.com/v", "text": "claude code", "published_at": None}]})


def test_parse_items_maps_fields_and_missing_date():
    e = parse_items(OK, "Web Hackathon VN")
    assert e[0]["source"] == "Web Hackathon VN" and e[0]["published"] > 0 and e[1]["published"] is None


def test_failed_channel_raises():
    with pytest.raises(RuntimeError):
        parse_items(json.dumps({"ok": False, "error": {"message": "broken"}}), "x")


def test_web_hackathon_source_is_forced_to_hackathons():
    got = select(parse_items(OK, "Web Hackathon VN"), set(), 1763078400 + 86400)
    assert [a["category"] for a in got] == ["hackathons"]


def test_undated_ignores_old_creation_date():
    assert parse_items(OK, "GitHub Search", undated=True)[0]["published"] is None
