"""Общий клиент LLM (OpenAI-compatible)."""

import json
import re

from openai import OpenAI

from aethermind.config import Settings


def get_client(settings: Settings | None = None) -> OpenAI:
    settings = settings or Settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY не задан. Скопируйте .env.example → .env")
    return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def chat_json(
    client: OpenAI,
    model: str,
    system: str,
    user: str,
) -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


def chat_text(
    client: OpenAI,
    model: str,
    system: str,
    user: str,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
    )
    return (response.choices[0].message.content or "").strip()


def extract_json_array(text: str) -> list:
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        return json.loads(match.group())
    return json.loads(text)
