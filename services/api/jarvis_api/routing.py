from dataclasses import dataclass

from .schemas import ProviderName


PROVIDER_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-5-mini", "gpt-4.1-mini"],
    "anthropic": ["claude-sonnet-4-5", "claude-haiku-4-5"],
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro"],
    "xai": ["grok-4-fast", "grok-3-mini"],
}


@dataclass(frozen=True)
class Route:
    provider: str
    model: str
    reason: str


def infer_task(text: str) -> str:
    normalized = text.lower()
    code_terms = ("código", "codigo", "code", "bug", "função", "script")
    if any(word in normalized for word in code_terms):
        return "code"
    if any(word in normalized for word in ("analise", "análise", "racioc", "compare", "planeje")):
        return "reasoning"
    if any(word in normalized for word in ("criativo", "campanha", "história", "story", "ideias")):
        return "creative"
    return "general"


PREFERENCE = {
    "code": ["anthropic", "openai", "xai", "gemini"],
    "reasoning": ["openai", "anthropic", "gemini", "xai"],
    "creative": ["gemini", "openai", "anthropic", "xai"],
    "general": ["openai", "gemini", "anthropic", "xai"],
}


def choose_route(
    requested: ProviderName,
    prompt: str,
    configured: set[str],
    model_override: str | None = None,
) -> Route | None:
    if requested != ProviderName.auto:
        provider = requested.value
        if provider not in configured:
            return None
        return Route(provider, model_override or PROVIDER_MODELS[provider][0], "seleção manual")

    task = infer_task(prompt)
    for provider in PREFERENCE[task]:
        if provider in configured:
            return Route(
                provider,
                model_override or PROVIDER_MODELS[provider][0],
                f"roteamento automático para tarefa do tipo {task}",
            )
    return None
