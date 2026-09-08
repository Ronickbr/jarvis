import ast
import re

from .schemas import RiskLevel, ToolCreate


HIGH_RISK_PERMISSIONS = {"filesystem:write", "network", "process", "secrets"}
CRITICAL_PATTERNS = (
    r"\brm\s+-rf\b",
    r"\b(shutdown|reboot|mkfs|format)\b",
    r"subprocess\.",
    r"child_process",
    r"os\.system",
)
NETWORK_PATTERNS = (r"\brequests\.", r"\bhttpx\.", r"\bfetch\(", r"https?://")


def classify_tool(tool: ToolCreate) -> RiskLevel:
    text = tool.code.lower()
    if any(re.search(pattern, text) for pattern in CRITICAL_PATTERNS):
        return RiskLevel.critical
    if HIGH_RISK_PERMISSIONS.intersection(tool.permissions):
        return RiskLevel.high
    if any(re.search(pattern, text) for pattern in NETWORK_PATTERNS):
        return RiskLevel.high
    if tool.permissions:
        return RiskLevel.medium
    return RiskLevel.low


def requires_confirmation(risk: RiskLevel) -> bool:
    return risk in {RiskLevel.high, RiskLevel.critical}


def validate_source(language: str, code: str) -> tuple[bool, str]:
    if language == "python":
        try:
            ast.parse(code)
        except SyntaxError as error:
            return False, f"Python inválido na linha {error.lineno}: {error.msg}"
        return True, "Sintaxe Python válida."

    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: list[str] = []
    for character in code:
        if character in pairs:
            stack.append(character)
        elif character in pairs.values():
            if not stack or pairs[stack.pop()] != character:
                return False, "Delimitadores JavaScript desbalanceados."
    if stack:
        return False, "Delimitadores JavaScript desbalanceados."
    return (
        True,
        "Validação estrutural JavaScript concluída; a sintaxe final será checada no sandbox.",
    )
