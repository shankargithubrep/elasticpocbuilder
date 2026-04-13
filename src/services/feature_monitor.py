"""
Feature Monitor

Fetches new Elastic product features from three sources:
  1. Elastic Blog RSS feed       — richest content, most curated
  2. GitHub Releases API         — elasticsearch + kibana repos
  3. elastic.co/what-is/new      — official "What's New" landing page

Returns a list of raw FeatureItem dicts for the curator to score.
No LLM calls here — pure fetch + parse.
"""

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BLOG_RSS_URL      = "https://www.elastic.co/blog/feed"
WHATS_NEW_URL     = "https://www.elastic.co/blog/whats-new-elastic-9-0-0"
GITHUB_REPOS      = ["elastic/elasticsearch", "elastic/kibana"]
GITHUB_API_BASE   = "https://api.github.com/repos"

REQUEST_TIMEOUT   = 15   # seconds
LOOKBACK_DAYS     = 14   # how far back to fetch (prevents re-processing old items)

BLOG_CATEGORIES_OF_INTEREST = {
    "release", "announcement", "launch", "new feature", "generally available",
    "ga", "preview", "beta", "inference", "search", "elasticsearch",
    "kibana", "observability", "security", "machine learning", "vector",
    "esql", "api", "dashboard", "agent", "rag",
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def fetch_all(lookback_days: int = LOOKBACK_DAYS) -> List[Dict[str, Any]]:
    """
    Fetch all sources and return a deduplicated list of raw feature dicts.
    Each dict has: id, title, url, source, published, summary, raw_text
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    items: List[Dict] = []

    for fetcher in (_fetch_blog_rss, _fetch_github_releases, _fetch_whats_new):
        try:
            batch = fetcher(cutoff)
            logger.info(f"{fetcher.__name__}: {len(batch)} items")
            items.extend(batch)
        except Exception as e:
            logger.warning(f"{fetcher.__name__} failed: {e}")

    # Deduplicate by url
    seen: set = set()
    unique = []
    for item in items:
        key = item.get("url", item.get("title", ""))
        if key not in seen:
            seen.add(key)
            unique.append(item)

    logger.info(f"Total unique items fetched: {len(unique)}")
    return unique


# ---------------------------------------------------------------------------
# Source 1: Elastic Blog RSS
# ---------------------------------------------------------------------------

def _fetch_blog_rss(cutoff: datetime) -> List[Dict]:
    resp = requests.get(BLOG_RSS_URL, timeout=REQUEST_TIMEOUT, headers=_ua())
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for entry in channel.findall("item"):
        title    = _text(entry, "title")
        url      = _text(entry, "link")
        pub_str  = _text(entry, "pubDate")
        summary  = _strip_html(_text(entry, "description"))
        cats     = [c.text.lower() for c in entry.findall("category") if c.text]

        pub_dt = _parse_rfc822(pub_str)
        if pub_dt and pub_dt < cutoff:
            continue

        # Filter to Elastic product / feature / release content
        if not _is_relevant_blog(title, cats):
            continue

        items.append({
            "id":       _make_id("blog", url or title),
            "title":    title,
            "url":      url,
            "source":   "elastic_blog",
            "published": pub_dt.isoformat() if pub_dt else "",
            "summary":  summary[:800],
            "raw_text": summary,
            "categories": cats,
        })

    return items


def _is_relevant_blog(title: str, cats: List[str]) -> bool:
    text = (title + " " + " ".join(cats)).lower()
    return any(kw in text for kw in BLOG_CATEGORIES_OF_INTEREST)


# ---------------------------------------------------------------------------
# Source 2: GitHub Releases (elasticsearch + kibana)
# ---------------------------------------------------------------------------

def _fetch_github_releases(cutoff: datetime) -> List[Dict]:
    items = []
    for repo in GITHUB_REPOS:
        try:
            url = f"{GITHUB_API_BASE}/{repo}/releases?per_page=10"
            resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=_ua())
            resp.raise_for_status()
            releases = resp.json()
            for r in releases:
                pub_str = r.get("published_at", "")
                pub_dt  = _parse_iso(pub_str)
                if pub_dt and pub_dt < cutoff:
                    continue
                if r.get("draft") or r.get("prerelease"):
                    continue  # skip drafts and alpha/RC builds

                body = r.get("body", "") or ""
                items.append({
                    "id":       _make_id("github", r.get("html_url", r.get("id", ""))),
                    "title":    f"{repo.split('/')[1].capitalize()} {r.get('tag_name', '')} Released",
                    "url":      r.get("html_url", ""),
                    "source":   "github_release",
                    "published": pub_dt.isoformat() if pub_dt else pub_str,
                    "summary":  _truncate_release_notes(body, 600),
                    "raw_text": body[:2000],
                    "categories": ["release", repo.split("/")[1]],
                })
        except Exception as e:
            logger.warning(f"GitHub release fetch failed for {repo}: {e}")

    return items


def _truncate_release_notes(body: str, max_chars: int) -> str:
    """Extract first meaningful paragraph from release notes markdown."""
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    # Skip lines that are just headers or bullet points with version numbers
    meaningful = [l for l in lines if len(l) > 30 and not l.startswith("##")]
    text = " ".join(meaningful[:5])
    return text[:max_chars]


# ---------------------------------------------------------------------------
# Source 3: elastic.co What's New page
# ---------------------------------------------------------------------------

def _fetch_whats_new(cutoff: datetime) -> List[Dict]:
    resp = requests.get(WHATS_NEW_URL, timeout=REQUEST_TIMEOUT, headers=_ua())
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    # The What's New page has <h2>/<h3> sections with feature descriptions
    for heading in soup.find_all(["h2", "h3"]):
        text = heading.get_text(strip=True)
        if not text or len(text) < 5:
            continue

        # Grab the following paragraph(s) as the description
        desc_parts = []
        sibling = heading.find_next_sibling()
        for _ in range(3):
            if sibling is None:
                break
            if sibling.name in ("h2", "h3"):
                break
            desc_parts.append(sibling.get_text(strip=True))
            sibling = sibling.find_next_sibling()

        summary = " ".join(desc_parts)[:600]
        if not summary:
            continue

        # Find nearest anchor link for URL
        anchor = heading.find("a")
        fragment = anchor["href"] if anchor and anchor.get("href") else ""
        url = WHATS_NEW_URL + fragment if fragment.startswith("#") else WHATS_NEW_URL

        items.append({
            "id":       _make_id("whats_new", text),
            "title":    text,
            "url":      url,
            "source":   "whats_new_page",
            "published": "",   # page doesn't have per-item dates
            "summary":  summary,
            "raw_text": summary,
            "categories": ["whats_new"],
        })

    return items[:20]   # cap — the page can be large


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _text(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _strip_html(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


def _make_id(source: str, value: str) -> str:
    h = hashlib.md5(value.encode()).hexdigest()[:10]
    return f"{source}_{h}"


def _ua() -> Dict[str, str]:
    return {"User-Agent": "ElasticDemoBuilder/1.0 (SA Feature Monitor)"}


def _parse_rfc822(s: str) -> Optional[datetime]:
    """Parse RSS pubDate like 'Mon, 01 Jan 2026 12:00:00 +0000'."""
    if not s:
        return None
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(s).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _parse_iso(s: str) -> Optional[datetime]:
    """Parse GitHub ISO8601 like '2026-03-20T10:00:00Z'."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None
