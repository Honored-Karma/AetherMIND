"""Агент 2: Аналитик — фильтрация шума, извлечение фактов."""

from aethermind.config import Settings
from aethermind.llm import chat_json, get_client
from aethermind.models import AnalysisResult, FactItem, PipelineConfig, RawArticle

SYSTEM_PROMPT = """Ты — жёсткий аналитик и фактчекер редакции AetherMind.

Задача: из сырого потока новостей отобрать только проверяемые факты, цифры и инсайды.
Отбрасывай: кликбейт, рекламу, спекуляции без источника, дубли, эмоциональный мусор.

Ответ строго в JSON:
{
  "summary": "1-2 предложения — суть дня по теме",
  "discarded_count": <число отброшенных материалов>,
  "facts": [
    {
      "claim": "краткий факт",
      "evidence": "почему это важно / контекст",
      "confidence": 0.0-1.0,
      "source_url": "url",
      "tags": ["тег1"]
    }
  ]
}

Правила:
- confidence < 0.5 — не включай
- максимум 12 фактов
- пиши на русском
"""


class AnalystAgent:
    def __init__(self, config: PipelineConfig, settings: Settings | None = None):
        self.config = config
        self.settings = settings or Settings()
        self.client = get_client(self.settings)

    def _format_articles(self, articles: list[RawArticle]) -> str:
        blocks = []
        for i, a in enumerate(articles, 1):
            blocks.append(
                f"--- Материал {i} ---\n"
                f"Источник: {a.source}\n"
                f"URL: {a.url}\n"
                f"Заголовок: {a.title}\n"
                f"Текст:\n{a.content[:2500]}\n"
            )
        return "\n".join(blocks)

    def run(self, articles: list[RawArticle]) -> AnalysisResult:
        if not articles:
            return AnalysisResult(topic=self.config.topic, facts=[], discarded_count=0, summary="Нет данных.")

        user_prompt = (
            f"Тема редакции: {self.config.topic}\n\n"
            f"Сырые материалы ({len(articles)} шт.):\n\n"
            f"{self._format_articles(articles)}"
        )

        data = chat_json(
            self.client,
            self.settings.openai_model,
            SYSTEM_PROMPT,
            user_prompt,
        )

        facts = [FactItem(**f) for f in data.get("facts", [])]
        return AnalysisResult(
            topic=self.config.topic,
            facts=facts,
            discarded_count=int(data.get("discarded_count", 0)),
            summary=data.get("summary", ""),
        )
