"""Keyword gate, categorisation and ranking (ported from the n8n "Tech News Processing" node)."""
import re

MAX_PER_CATEGORY = 12
MAX_PER_SOURCE = 3
MAX_PER_FORCED_SOURCE = 6
MAX_TOTAL = 80
AGE_DAYS = {"default": 3, "hackathons": 45}

_KW = r"""\bai\b|\bllms?\b|\bgenerative ai\b|\bmachine learning\b|\bopenai\b|\banthropic\b|\bclaude\b|\bgemini\b
|\bgpt-?\d*\b|\bmcp\b|\bagentic\b|\bai agents?\b|\bcoding agents?\b|\bagent skills?\b|\bprompt injection\b|\bcopilot\b
|\bdevsecops\b|\bdevops\b|\bcybersecurity\b|\bcves?\b|\bvulnerabilit(?:y|ies)\b|\bzero[- ]days?\b|\bsupply[- ]chain\b
|\bsbom\b|\bransomware\b|\bexploit(?:s|ed)?\b|\bkubernetes\b|\bk8s\b|\bterraform\b|\bopentofu\b|\bdocker\b|\bci/cd\b
|\bgitops\b|\bsre\b|\bobservability\b|\binfrastructure\b|\bplatform engineering\b|\bserverless\b|\bcloud\b|\baws\b
|\bazure\b|\bgcp\b|\bcloudflare\b|\bsemiconductors?\b|\bbackend\b|\bfront-?end\b|\bfull-?stack\b|\breact\b
|\bnext\.js\b|\btypescript\b|\bnode\.js\b|\bpostgres(?:ql)?\b|\brust\b|\bapis?\b|\bopen[- ]source\b|\bdevelopers?\b
|\bstartups?\b"""
KEYWORDS = [re.compile(p, re.IGNORECASE) for p in re.split(r"\|(?=\\b)", _KW.replace("\n", ""))]  # one regex per keyword

def _table(rows):
    return [(re.compile(p), v) for p, v in rows]

FORCED = _table([
    (r"^(Product Hunt|Show HN|dev\.to #buildinpublic)$", "build-in-public"),
    (r"^(GitHub Trending|GitHub Open Source|GitHub Search|dev\.to #opensource|OpenSSF)$", "opensource"),
    (r"^(Google News:|Web Hackathon)", "hackathons"),
    (r"^(Claude Code Releases|Anthropic .*)$", "ai-agents"),
])
DEFAULT_BY_SOURCE = _table([
    (r"^(Google Cloud|AWS News|AWS Architecture Blog|Azure|Cloudflare|Kubernetes|CNCF|Docker|HashiCorp|dev\.to #kubernetes|dev\.to #aws)$", "cloud-infra"),
    (r"^(BleepingComputer|The Hacker News|Snyk|GitGuardian|Trail of Bits|GitHub Security Lab|AWS Security Blog|Datadog Security Labs|Unit 42|Krebs on Security|Chainguard|dev\.to #devsecops)$", "security"),
    (r"^(Simon Willison|Latent Space|Hugging Face)$", "ai-agents"),
    (r"^(GitHub Blog|Vercel)$", "fullstack"),
])
REQUIRE = {"hackathons": re.compile(r"hackathon|cuộc thi|thi lập trình|competition|contest", re.IGNORECASE)}
SECURITY = re.compile(r"\b(cves?|vulnerabilit(?:y|ies)|zero[- ]days?|ransomware|malware|exploit(?:s|ed)?|devsecops"
                      r"|supply[- ]chain|sbom|phishing|data breach|cybersecurity|prompt injection)\b", re.IGNORECASE)
RULES = [(re.compile(p, re.IGNORECASE), c) for p, c in [
    (r"\b(ai|llms?|claude|anthropic|gemini|gpt-?\d*|mcp|agentic|agents?|copilot|openai)\b", "ai-agents"),
    (r"\b(kubernetes|k8s|terraform|opentofu|docker|ci/cd|devops|sre|cloud|aws|azure|gcp|serverless|infrastructure|observability|gitops)\b", "cloud-infra"),
    (r"\b(react|next\.js|typescript|node\.js|front-?end|back-?end|full-?stack|postgres(?:ql)?|rust|apis?)\b", "fullstack"),
    (r"\bopen[- ]source\b", "opensource"),
]]
EXCLUDE = [re.compile(p, re.IGNORECASE) for p in [
    r"\b(car|auto|automotive|engine|appliance|plumbing|hvac|furniture|screen|battery)\s+(repair|maintenance)\b",
    r"\b(best|top)\s+\w*\s*deals?\b",
    r"\b(coupons?|promo codes?|discount codes?)\b",
    r"\b(black friday|cyber monday|prime day)\b",
]]
PROTECT = re.compile(r"\b(cloud services?|bug fix(?:es)?|security (?:fix(?:es)?|patch(?:es)?)|hotfix(?:es)?)\b", re.IGNORECASE)


def strip(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(s or ""))).strip()


def first(table, s):
    return next((v for rx, v in table if rx.search(s)), None)


def select(entries, known, now):
    """Filter, categorise and rank entries; `known` is the set of URLs already stored."""
    seen, ranked = set(known), []
    for e in entries:
        title, url = strip(e["title"]), str(e["url"]).strip()
        if not title or not re.match(r"https?://", url) or url in seen:
            continue
        seen.add(url)
        source, body = e["source"], strip(e["body"])
        text = f"{title} {body}"
        if not PROTECT.search(text) and any(r.search(text) for r in EXCLUDE):
            continue
        forced = first(FORCED, source)
        if forced in REQUIRE and not REQUIRE[forced].search(text):
            continue
        kw = sum(2 if r.search(title) else 1 if r.search(body) else 0 for r in KEYWORDS)
        if not forced and kw == 0:
            continue
        published = e["published"] or now
        sec = SECURITY.search(title) or len(SECURITY.findall(text)) >= 2
        category = forced or ("security" if sec else first(DEFAULT_BY_SOURCE, source)
                              or first(RULES, text) or "general")
        if published < now - AGE_DAYS.get(category, AGE_DAYS["default"]) * 86400:
            continue
        ranked.append({"title": title, "description": body[:500], "url": url, "source": source,
                       "category": category, "published": published, "forced": bool(forced),
                       "score": kw + (3 if forced else 0)})
    ranked.sort(key=lambda a: (-a["score"], -a["published"]))
    per_cat, per_src, picked = {}, {}, []
    for a in ranked:
        cap = MAX_PER_FORCED_SOURCE if a["forced"] else MAX_PER_SOURCE
        if per_cat.get(a["category"], 0) >= MAX_PER_CATEGORY or per_src.get(a["source"], 0) >= cap:
            continue
        per_cat[a["category"]] = per_cat.get(a["category"], 0) + 1
        per_src[a["source"]] = per_src.get(a["source"], 0) + 1
        picked.append(a)
    return picked[:MAX_TOTAL]
