import time

from tech_news import filters as news

NOW = time.time()


def entry(title, source="Hacker News", body="", url=None, age_days=0):
    return {"title": title, "url": url or f"https://x.test/{abs(hash(title))}", "source": source,
            "body": body, "published": NOW - age_days * 86400}


def test_keyword_gate_and_noise():
    got = news.select([entry("Kubernetes 1.40 released"), entry("Celebrity gossip today"),
                       entry("Best laptop deals this week with AI")], set(), NOW)
    assert [a["title"] for a in got] == ["Kubernetes 1.40 released"]


def test_known_urls_and_age_dropped():
    old = entry("Docker news", age_days=10)
    known = entry("Terraform news", url="https://x.test/known")
    assert news.select([old, known, entry("Rust news")], {"https://x.test/known"}, NOW)[0]["title"] == "Rust news"
    assert len(news.select([old, known, entry("Rust news")], {"https://x.test/known"}, NOW)) == 1


def test_forced_and_default_categories():
    got = {a["source"]: a["category"] for a in news.select([
        entry("My SaaS launch", source="Product Hunt"),
        entry("A repo", source="GitHub Trending"),
        entry("Patch for CVE-2026-1", source="Docker"),
        entry("Update", source="AWS News", body="cloud stuff"),
    ], set(), NOW)}
    assert got == {"Product Hunt": "build-in-public", "GitHub Trending": "opensource",
                   "Docker": "security", "AWS News": "cloud-infra"}


def test_hackathon_needs_contest_word_and_lives_45_days():
    items = [entry("Weather in Hanoi", source="Google News: Hackathon VN"),
             entry("Hackathon AI Việt Nam 2026", source="Google News: Hackathon VN", age_days=30)]
    assert [a["title"] for a in news.select(items, set(), NOW)] == ["Hackathon AI Việt Nam 2026"]


def test_per_source_cap():
    items = [entry(f"Kubernetes post {i}", source="InfoQ") for i in range(6)]
    assert len(news.select(items, set(), NOW)) == news.MAX_PER_SOURCE


def test_opensource_capped_below_default():
    CATEGORY_CAP = news.CATEGORY_CAP
    now = 1_763_000_000
    es = [{"title": f"repo{i}", "url": f"https://github.com/o/r{i}", "source": "GitHub Trending", "body": "x", "published": now}
          for i in range(30)]
    es += [{"title": f"r{i}", "url": f"https://github.com/p/r{i}", "source": "GitHub Open Source", "body": "x", "published": now}
           for i in range(30)]
    assert len([a for a in news.select(es, set(), now) if a["category"] == "opensource"]) == CATEGORY_CAP["opensource"]


def test_release_feeds_are_forced_into_releases():
    from tech_news.filters import select
    now = time.time()
    e = {"title": "v2.1.0", "url": "https://github.com/x/y/releases/tag/v2.1.0", "source": "Release: Claude Code",
         "body": "fixes", "published": now}
    assert select([e], set(), now)[0]["category"] == "releases"
