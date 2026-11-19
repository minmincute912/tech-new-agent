import json

from tech_news import brief
from tech_news.site import build
from tech_news.store import append_rows

DAY = "2026-11-19"


def row(i, cat="security", sig=3, source="x", title="T"):
    return {"title": f"{title}{i}", "summary": "s", "url": f"https://e.com/{i}", "source": source, "category": cat,
            "significance": sig, "published_at": f"{DAY}T05:00:00+00:00", "processed_at": f"{DAY}T05:00:00+00:00",
            "requires_review": False}


def test_top_of_day_limits_per_category_and_skips_light_and_other_days():
    rows = [row(i, "security", 5) for i in range(5)] + [row(10, "cloud-infra", 2), row(11, "opensource", 5),
                                                         {**row(12), "published_at": "2026-11-18T05:00:00+00:00"}]
    top = brief.top_of_day(rows, DAY, n=10, per_cat=2)
    assert [r["category"] for r in top] == ["security", "security", "cloud-infra"]


def test_format_message_escapes_html_and_stays_under_limit():
    top = [row(i, title="<b>&x " + "y" * 200) for i in range(8)]
    msg = brief.format_message(DAY, top, "https://s.example")
    assert "&lt;b&gt;" in msg and "<b>&x" not in msg
    assert len(msg) <= 4096


def test_notify_sends_once_and_skips_without_token(tmp_path, monkeypatch):
    monkeypatch.setattr(brief, "BRIEFS_FILE", tmp_path / "briefs.json")
    monkeypatch.setattr(brief, "load_briefs", lambda path=tmp_path / "briefs.json": json.loads(path.read_text()) if path.exists() else {})
    monkeypatch.setattr(brief, "save_briefs", lambda b, path=tmp_path / "briefs.json": path.write_text(json.dumps(b)))
    sent = []
    send = lambda *a: sent.append(a)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    brief.notify(send, rows=[row(1)], day=DAY)
    assert sent == []
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@chan")
    brief.notify(send, rows=[row(1)], day=DAY)
    brief.notify(send, rows=[row(1)], day=DAY)
    assert len(sent) == 1 and sent[0][2] == "@chan"


def test_build_exposes_telegram_link(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@technews")
    (tmp_path / "data").mkdir()
    append_rows([row(1)], tmp_path / "data")
    build(tmp_path / "data", tmp_path / "public")
    out = json.loads((tmp_path / "public" / "data.json").read_text())
    assert "briefs" not in out and out["telegram"] == "https://t.me/technews"
