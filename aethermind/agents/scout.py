"""Агент 1: Скаут — сбор сырого контента из источников."""

import asyncio
from datetime import datetime

import httpx

from aethermind.models import PipelineConfig, RawArticle, SourceConfig, SourceType
from aethermind.sources.fetchers import fetch_source

# Доверенные RSS по темам (авто-поиск)
TRUSTED_FEEDS: dict[str, list[SourceConfig]] = {
    "crypto": [
        SourceConfig(type=SourceType.RSS, url="https://cointelegraph.com/rss", label="CoinTelegraph"),
        SourceConfig(type=SourceType.RSS, url="https://www.coindesk.com/arc/outboundfeeds/rss/", label="CoinDesk"),
        SourceConfig(type=SourceType.REDDIT, url="https://www.reddit.com/r/CryptoCurrency", label="r/CryptoCurrency"),
    ],
    "ai": [
        SourceConfig(type=SourceType.RSS, url="https://www.technologyreview.com/feed/", label="MIT Tech Review"),
        SourceConfig(type=SourceType.RSS, url="https://venturebeat.com/category/ai/feed/", label="VentureBeat AI"),
        SourceConfig(type=SourceType.REDDIT, url="https://www.reddit.com/r/MachineLearning", label="r/MachineLearning"),
    ],
    "gaming": [
        SourceConfig(type=SourceType.RSS, url="https://www.polygon.com/rss/index.xml", label="Polygon"),
        SourceConfig(type=SourceType.RSS, url="https://www.gamesindustry.biz/feed", label="GamesIndustry"),
        SourceConfig(type=SourceType.REDDIT, url="https://www.reddit.com/r/Games", label="r/Games"),
    ],
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "crypto": ["crypto", "крипт", "defi", "bitcoin", "блокчейн", "btc", "eth"],
    "ai": ["ai", "ии", "машинн", "neural", "gpt", "llm", "нейросет"],
    "gaming": ["gaming", "game", "игр", "гейм", "esport"],
}


def _topic_key(topic: str) -> str | None:
    lower = topic.lower()
    for key, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return key
    return None


class ScoutAgent:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def _resolve_sources(self) -> list[SourceConfig]:
        if self.config.sources:
            return self.config.sources
        if self.config.auto_discover:
            key = _topic_key(self.config.topic)
            if key:
                return TRUSTED_FEEDS[key]
        return []

    async def run(self) -> list[RawArticle]:
        sources = self._resolve_sources()
        if not sources:
            raise ValueError(
                "Нет источников: укажите sources в конфиге или включите auto_discover с известной темой "
                "(crypto, ai, gaming)."
            )

        articles: list[RawArticle] = []
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            tasks = [fetch_source(src, client) for src in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for src, result in zip(sources, results):
                if isinstance(result, Exception):
                    print(f"[Скаут] Ошибка {src.url}: {result}")
                    continue
                articles.extend(result)

        articles.sort(
            key=lambda a: a.published_at or datetime.min,
            reverse=True,
        )
        return articles[: self.config.max_articles]
