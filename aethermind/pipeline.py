"""Оркестратор пайплайна: Скаут → Аналитик → Спичрайтер."""

import asyncio
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from aethermind.agents.analyst import AnalystAgent
from aethermind.agents.scout import ScoutAgent
from aethermind.agents.writer import WriterAgent
from aethermind.config import Settings, load_pipeline_config
from aethermind.models import AnalysisResult, PipelineConfig, RawArticle, Report
from aethermind.outputs.delivery import save_markdown, send_discord, send_telegram

console = Console()


@dataclass
class PipelineResult:
    articles: list[RawArticle]
    analysis: AnalysisResult
    report: Report
    output_path: Path | None = None


class Pipeline:
    def __init__(self, config: PipelineConfig, settings: Settings | None = None):
        self.config = config
        self.settings = settings or Settings()
        self.scout = ScoutAgent(config)
        self.analyst = AnalystAgent(config, self.settings)
        self.writer = WriterAgent(config, self.settings)

    async def run(self) -> PipelineResult:
        console.print(Panel("[bold cyan]Скаут[/] собирает данные…", title="AetherMind"))
        articles = await self.scout.run()
        console.print(f"  → {len(articles)} материалов")

        console.print(Panel("[bold yellow]Аналитик[/] фильтрует факты…", title="AetherMind"))
        analysis = self.analyst.run(articles)
        console.print(f"  → {len(analysis.facts)} фактов, отброшено ~{analysis.discarded_count}")

        console.print(Panel("[bold green]Спичрайтер[/] оформляет отчёт…", title="AetherMind"))
        report = self.writer.run(analysis)

        output_path = save_markdown(report, self.config.output_dir)
        console.print(f"  → сохранено: [underline]{output_path}[/]")

        if self.config.deliver_telegram:
            await send_telegram(report, self.settings)
            console.print("  → отправлено в Telegram")

        if self.config.deliver_discord:
            await send_discord(report, self.settings)
            console.print("  → отправлено в Discord")

        return PipelineResult(
            articles=articles,
            analysis=analysis,
            report=report,
            output_path=output_path,
        )


async def run_from_config(path: str | Path) -> PipelineResult:
    config = load_pipeline_config(path)
    pipeline = Pipeline(config)
    return await pipeline.run()
