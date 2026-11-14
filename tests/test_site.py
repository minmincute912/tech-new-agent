import json
from datetime import datetime, timezone

from tech_news.site import build
from tech_news.store import append_rows


def test_build_hides_noise_and_dedups(tmp_path):
    now = datetime.now(timezone.utc).isoformat()
    row = lambda u, c: {"title": u, "summary": "s", "url": u, "source": "x", "category": c, "significance": 3,
                        "published_at": now, "processed_at": now, "requires_review": False}
    append_rows([row("a", "security"), row("b", "noise"), row("a", "security")], tmp_path / "data")
    build(tmp_path / "data", tmp_path / "public")
    out = json.loads((tmp_path / "public" / "data.json").read_text())
    assert [a["url"] for a in out["articles"]] == ["a"]
    assert (tmp_path / "public" / "index.html").exists()
