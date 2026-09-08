from jarvis_api.policy import classify_tool, requires_confirmation
from jarvis_api.schemas import RiskLevel, ToolCreate


def tool(code: str, permissions: list[str] | None = None) -> ToolCreate:
    return ToolCreate(
        name="sample_tool",
        description="Uma ferramenta de teste segura.",
        code=code,
        permissions=permissions or [],
    )


def test_plain_function_is_low_risk() -> None:
    assert classify_tool(tool("print('olá')")) == RiskLevel.low


def test_destructive_code_is_critical() -> None:
    risk = classify_tool(tool("import os\nos.system('rm -rf /tmp/example')"))
    assert risk == RiskLevel.critical
    assert requires_confirmation(risk)


def test_network_permission_is_high_risk() -> None:
    assert classify_tool(tool("print('ok')", ["network"])) == RiskLevel.high
