from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from aethermind.models import DEFAULT_WRITER_STYLE, PipelineConfig, SourceConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""


def load_pipeline_config(path: str | Path) -> PipelineConfig:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    sources = [SourceConfig(**s) for s in data.get("sources", [])]
    return PipelineConfig(
        topic=data["topic"],
        sources=sources,
        auto_discover=data.get("auto_discover", False),
        max_articles=data.get("max_articles", 20),
        output_dir=data.get("output_dir", "output"),
        deliver_telegram=data.get("deliver_telegram", False),
        deliver_discord=data.get("deliver_discord", False),
        writer_style=data.get("writer_style", DEFAULT_WRITER_STYLE),
    )
