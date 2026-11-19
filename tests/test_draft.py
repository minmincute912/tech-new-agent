from datetime import datetime, timezone

from tech_news import brief, draft

NOW = datetime(2026, 11, 22, tzinfo=timezone.utc)


def row(i, sig=3, day="2026-11-20"):
    return {"title": f"T{i}", "summary": "s", "url": f"u{i}", "source": "x", "category": "ai-agents", "significance": sig,
            "published_at": f"{day}T05:00:00+00:00", "kind": "tool", "action": "Thử"}


def test_week_top_ranks_by_significance_and_skips_old_or_low():
    rows = [row(1, 3), row(2, 5), row(3, 2), row(4, 4, "2026-11-01")]
    assert [r["url"] for r in draft.week_top(rows, NOW)] == ["u2", "u1"]


def test_draft_sends_plain_text_to_channel_and_skips_without_chat(monkeypatch):
    sent = []
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    draft.draft([row(1), row(2), row(3)], call=lambda *a: "ý 1", send_fn=lambda *a: sent.append(a), provs=[{"name": "a"}])
    assert sent == []
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(draft, "week_top", lambda rows, now=None, n=10: rows)
    draft.draft([row(1), row(2), row(3)], call=lambda *a: "ý 1", send_fn=lambda *a: sent.append(a), provs=[{"name": "a"}])
    assert sent[0][2] == "42" and sent[0][3] is None and "ý 1" in sent[0][0]


def test_digest_shows_action_line():
    msg = brief.format_message("2026-11-19", [row(1)], "https://s.example")
    assert "→ Thử" in msg
