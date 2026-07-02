from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    RSS = "rss"
    REDDIT = "reddit"
    WEB = "web"


class SourceConfig(BaseModel):
    type: SourceType
    url: str
    label: str | None = None
    max_items: int = 10


class RawArticle(BaseModel):
    """Сырой материал от Скаута."""

    title: str
    content: str
    url: str
    source: str
    published_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FactItem(BaseModel):
    """Отфильтрованный факт от Аналитика."""

    claim: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_url: str
    tags: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    topic: str
    facts: list[FactItem]
    discarded_count: int = 0
    summary: str = ""


class ReportFormat(str, Enum):
    MARKDOWN = "markdown"
    TELEGRAM = "telegram"
    DISCORD = "discord"


class Report(BaseModel):
    title: str
    body: str
    format: ReportFormat = ReportFormat.MARKDOWN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    topic: str = ""


DEFAULT_WRITER_STYLE = (
    "Лаконичный аналитический стиль: факты, цифры, без кликбейта. "
    "Структура: заголовок, краткий лид, блоки по темам, вывод."
)


class PipelineConfig(BaseModel):
    topic: str
    sources: list[SourceConfig] = Field(default_factory=list)
    auto_discover: bool = False
    max_articles: int = 20
    output_dir: str = "output"
    deliver_telegram: bool = False
    deliver_discord: bool = False
    writer_style: str = DEFAULT_WRITER_STYLE
