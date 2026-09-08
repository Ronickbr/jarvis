import time
from typing import Any

import httpx

from .config import Settings
from .routing import Route
from .schemas import ChatMessage, ChatResponse


SYSTEM_PROMPT = (
    "Você é Jarvis, um assistente pessoal preciso, elegante e eficiente. "
    "Use sarcasmo sutil somente quando apropriado. "
    "Não afirme ter executado ações que não executou. "
    "Peça confirmação antes de qualquer ação sensível ou destrutiva."
)


def configured_providers(settings: Settings) -> set[str]:
    mapping = {
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "gemini": settings.gemini_api_key,
        "xai": settings.xai_api_key,
    }
    return {name for name, key in mapping.items() if key}


async def complete(
    route: Route, messages: list[ChatMessage], settings: Settings, personality: str
) -> ChatResponse:
    started = time.perf_counter()
    prompt = f"{SYSTEM_PROMPT}\nPersonalidade configurada: {personality}."
    if route.provider in {"openai", "xai"}:
        content = await _openai_compatible(route, messages, settings, prompt)
    elif route.provider == "anthropic":
        content = await _anthropic(route, messages, settings, prompt)
    else:
        content = await _gemini(route, messages, settings, prompt)
    return ChatResponse(
        content=content,
        provider=route.provider,
        model=route.model,
        reason=route.reason,
        latency_ms=round((time.perf_counter() - started) * 1000),
    )


async def _openai_compatible(
    route: Route, messages: list[ChatMessage], settings: Settings, system: str
) -> str:
    is_xai = route.provider == "xai"
    key = settings.xai_api_key if is_xai else settings.openai_api_key
    base = "https://api.x.ai/v1" if is_xai else "https://api.openai.com/v1"
    payload: dict[str, Any] = {
        "model": route.model,
        "messages": [{"role": "system", "content": system}]
        + [message.model_dump() for message in messages],
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def _anthropic(
    route: Route, messages: list[ChatMessage], settings: Settings, system: str
) -> str:
    converted = [
        {"role": message.role, "content": message.content}
        for message in messages
        if message.role != "system"
    ]
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key or "",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": route.model,
                "system": system,
                "messages": converted,
                "max_tokens": 2048,
            },
        )
        response.raise_for_status()
        return "".join(
            block["text"]
            for block in response.json()["content"]
            if block["type"] == "text"
        )


async def _gemini(
    route: Route, messages: list[ChatMessage], settings: Settings, system: str
) -> str:
    contents = [
        {
            "role": "model" if message.role == "assistant" else "user",
            "parts": [{"text": message.content}],
        }
        for message in messages
        if message.role != "system"
    ]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{route.model}:generateContent"
    )
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            url,
            params={"key": settings.gemini_api_key},
            json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents},
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def demo_response(user_text: str) -> ChatResponse:
    excerpt = user_text.strip().replace("\n", " ")[:140]
    return ChatResponse(
        content=(
            "Modo demonstração ativo. Posso estruturar este pedido, mas preciso de ao menos uma "
            f"chave de provedor para gerar a resposta real. Pedido recebido: “{excerpt}”"
        ),
        provider="demo",
        model="local-deterministic",
        reason="nenhum provedor configurado",
        latency_ms=0,
        demo=True,
    )
