"""Сохранение и доставка отчётов."""

from datetime import datetime
from pathlib import Path

import httpx

from aethermind.config import Settings
from aethermind.models import Report


def save_markdown(report: Report, output_dir: str | Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = report.created_at.strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c if c.isalnum() else "_" for c in report.topic[:40])
    path = output_dir / f"{stamp}_{safe_topic}.md"

    content = f"# {report.title}\n\n"
    content += f"> Сгенерировано AetherMind · {report.created_at.isoformat()} UTC\n\n"
    content += report.body

    path.write_text(content, encoding="utf-8")
    return path


async def send_telegram(report: Report, settings: Settings) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID обязательны для доставки в Telegram")

    text = f"*{report.title}*\n\n{report.body}"
    if len(text) > 4000:
        text = text[:3990] + "\n\n…"

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
        )
        response.raise_for_status()


async def send_discord(report: Report, settings: Settings) -> None:
    if not settings.discord_webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL обязателен для доставки в Discord")

    content = f"**{report.title}**\n\n{report.body}"
    if len(content) > 1900:
        content = content[:1890] + "\n\n…"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.discord_webhook_url,
            json={"content": content},
        )
        response.raise_for_status()
