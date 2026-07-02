"""CLI для AetherMind."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from aethermind.pipeline import run_from_config

app = typer.Typer(
    name="aethermind",
    help="AetherMind — автономная редакция: Скаут → Аналитик → Спичрайтер",
)
console = Console()


@app.command()
def run(
    config: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Путь к YAML-конфигу пайплайна",
    ),
):
    """Запустить полный цикл редакции."""
    try:
        result = asyncio.run(run_from_config(config))
        console.print(f"\n[bold green]Готово![/] Отчёт: {result.output_path}")
    except Exception as exc:
        console.print(f"[bold red]Ошибка:[/] {exc}")
        raise typer.Exit(1) from exc


def main():
    app()


if __name__ == "__main__":
    main()
