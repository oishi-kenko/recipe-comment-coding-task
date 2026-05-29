"""OpenAI API クライアントのラッパー。

messages を渡すと生成されたテキストが返る。

    from app import llm
    text = llm.generate([
        {"role": "system", "content": "..."},
        {"role": "user",   "content": "..."},
    ])
"""

from __future__ import annotations

from openai import OpenAI

from app import config

_client: OpenAI | None = None


def is_configured() -> bool:
    """API キーが設定されているか。"""
    return bool(config.OPENAI_API_KEY)


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not is_configured():
            raise RuntimeError("OPENAI_API_KEY が設定されていません。.env を確認してください。")
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def generate(messages: list[dict], *, temperature: float = 0.7) -> str:
    """messages からテキストを生成して返す。"""
    response = _get_client().chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()
