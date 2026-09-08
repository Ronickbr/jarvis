from jarvis_api.routing import choose_route, infer_task
from jarvis_api.schemas import ProviderName


def test_detects_code_task() -> None:
    assert infer_task("Crie uma função Python") == "code"


def test_auto_never_chooses_unconfigured_provider() -> None:
    route = choose_route(ProviderName.auto, "Escreva código", {"gemini"})
    assert route is not None
    assert route.provider == "gemini"


def test_manual_unconfigured_provider_is_refused() -> None:
    assert choose_route(ProviderName.openai, "Olá", set()) is None
