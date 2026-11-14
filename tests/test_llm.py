import time

import pytest

from tech_news import llm as news

NOW = time.time()

BATCH = [{"title": "T1", "source": "InfoQ", "description": "d", "url": "u1", "category": "general",
          "forced": False, "published": NOW},
         {"title": "T2", "source": "Product Hunt", "description": "d", "url": "u2", "category": "build-in-public",
          "forced": True, "published": NOW}]
GOOD = '```json\n[{"id":1,"category":"security","vietnamese_title":"V1","summary":"s","significance":4},' \
       '{"id":2,"category":"general","vietnamese_title":"V2","summary":"s","significance":2}]\n```'


def test_parse_ai_keeps_forced_category_and_flags_review():
    rows = news.parse_ai(GOOD, BATCH, "2026-11-13T00:00:00+00:00")
    assert [r["category"] for r in rows] == ["security", "build-in-public"]
    assert [r["requires_review"] for r in rows] == [True, False]


def test_parse_ai_skips_invalid_item_and_rejects_garbage():
    partial = '[{"id":1,"category":"x","vietnamese_title":"V","summary":"s","significance":3},{"id":2}]'
    rows = news.parse_ai(partial, BATCH, "t")
    assert len(rows) == 1 and rows[0]["category"] == "general"  # bad slug falls back to rule category
    with pytest.raises(ValueError):
        news.parse_ai("sorry, I cannot", BATCH, "t")


def test_fallback_provider_used_when_primary_fails():
    calls = []

    def call(p, system, user):
        calls.append(p["name"])
        if p["name"] == "gemini":
            raise RuntimeError("429")
        return GOOD

    rows = news.classify_batch(BATCH, "sys", [{"name": "gemini"}, {"name": "openrouter"}], "t", call=call, wait=0)
    assert len(rows) == 2 and calls == ["gemini", "gemini", "openrouter"]


def test_all_providers_fail_returns_none():
    def call(p, s, u):
        raise RuntimeError("down")
    assert news.classify_batch(BATCH, "s", [{"name": "a"}], "t", call=call, wait=0) is None
