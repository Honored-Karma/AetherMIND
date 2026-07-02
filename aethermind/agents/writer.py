"""Агент 3: Спичрайтер — упаковка в готовый отчёт."""

from datetime import datetime

from aethermind.config import Settings
from aethermind.llm import chat_text, get_client
from aethermind.models import AnalysisResult, PipelineConfig, Report, ReportFormat

SYSTEM_TEMPLATE = """Ты — спичрайтер редакции AetherMind.

Стиль: {style}

Собери финальный материал в Markdown:
- цепляющий, но честный заголовок (H1)
- лид на 2-3 предложения
- секции с подзаголовками (##)
- списки фактов где уместно
- блок «Вывод» в конце
- без кликбейта и воды
- язык: русский

В начале ответа напиши строку TITLE: <заголовок>
Затем пустая строка и тело отчёта в Markdown.
"""


class WriterAgent:
    def __init__(self, config: PipelineConfig, settings: Settings | None = None):
        self.config = config
        self.settings = settings or Settings()
        self.client = get_client(self.settings)

    def _format_analysis(self, analysis: AnalysisResult) -> str:
        lines = [f"Тема: {analysis.topic}", f"Сводка аналитика: {analysis.summary}", "", "Факты:"]
        for f in analysis.facts:
            lines.append(
                f"- {f.claim} (уверенность {f.confidence:.0%}, источник: {f.source_url})\n"
                f"  Контекст: {f.evidence}"
            )
        return "\n".join(lines)

    def run(self, analysis: AnalysisResult) -> Report:
        system = SYSTEM_TEMPLATE.format(style=self.config.writer_style)
        user = self._format_analysis(analysis)

        raw = chat_text(self.client, self.settings.openai_model, system, user)

        title = analysis.topic
        body = raw
        if raw.startswith("TITLE:"):
            first_line, _, rest = raw.partition("\n")
            title = first_line.replace("TITLE:", "").strip()
            body = rest.strip()

        return Report(
            title=title,
            body=body,
            format=ReportFormat.MARKDOWN,
            created_at=datetime.utcnow(),
            topic=analysis.topic,
        )
