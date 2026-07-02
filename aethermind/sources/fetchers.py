from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from aethermind.models import RawArticle, SourceConfig, SourceType

USER_AGENT = "AetherMind/0.1 (+https://github.com/aethermind)"


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def _strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:80])


async def fetch_rss(source: SourceConfig, client: httpx.AsyncClient) -> list[RawArticle]:
    label = source.label or urlparse(source.url).netloc
    response = await client.get(source.url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    feed = feedparser.parse(response.text)
    articles: list[RawArticle] = []

    for entry in feed.entries[: source.max_items]:
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = _strip_html(entry.content[0].value)
        elif hasattr(entry, "summary"):
            content = _strip_html(entry.summary)
        articles.append(
            RawArticle(
                title=entry.get("title", "Без заголовка"),
                content=content,
                url=entry.get("link", source.url),
                source=label,
                published_at=_parse_date(entry.get("published")),
            )
        )
    return articles


async def fetch_reddit(source: SourceConfig, client: httpx.AsyncClient) -> list[RawArticle]:
    label = source.label or source.url
    url = source.url.rstrip("/")
    if not url.endswith(".json"):
        url = f"{url}/hot.json?limit={source.max_items}"

    response = await client.get(url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    data = response.json()
    articles: list[RawArticle] = []

    for child in data.get("data", {}).get("children", [])[: source.max_items]:
        post = child.get("data", {})
        body = post.get("selftext") or post.get("title", "")
        articles.append(
            RawArticle(
                title=post.get("title", "Без заголовка"),
                content=body[:4000],
                url=f"https://reddit.com{post.get('permalink', '')}",
                source=label,
                published_at=datetime.fromtimestamp(
                    post.get("created_utc", 0), tz=timezone.utc
                ),
                metadata={"score": post.get("score"), "subreddit": post.get("subreddit")},
            )
        )
    return articles


async def fetch_web(source: SourceConfig, client: httpx.AsyncClient) -> list[RawArticle]:
    label = source.label or urlparse(source.url).netloc
    response = await client.get(source.url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else label
    content = _strip_html(response.text)
    return [
        RawArticle(
            title=title,
            content=content[:6000],
            url=source.url,
            source=label,
        )
    ]


async def fetch_source(source: SourceConfig, client: httpx.AsyncClient) -> list[RawArticle]:
    if source.type == SourceType.RSS:
        return await fetch_rss(source, client)
    if source.type == SourceType.REDDIT:
        return await fetch_reddit(source, client)
    if source.type == SourceType.WEB:
        return await fetch_web(source, client)
    raise ValueError(f"Неизвестный тип источника: {source.type}")
