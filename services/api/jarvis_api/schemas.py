from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ToolStatus(StrEnum):
    draft = "draft"
    validated = "validated"
    approved = "approved"
    enabled = "enabled"
    disabled = "disabled"


class ProviderName(StrEnum):
    auto = "auto"
    openai = "openai"
    anthropic = "anthropic"
    gemini = "gemini"
    xai = "xai"


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=50_000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=100)
    provider: ProviderName = ProviderName.auto
    model: str | None = None
    personality: str = Field(default="elegant", max_length=80)


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str
    reason: str
    latency_ms: int
    demo: bool = False


class ProviderStatus(BaseModel):
    name: str
    configured: bool
    models: list[str]


class ToolCreate(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    description: str = Field(min_length=5, max_length=500)
    language: Literal["python", "javascript"] = "python"
    code: str = Field(min_length=1, max_length=100_000)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)


class ToolRecord(ToolCreate):
    id: str
    status: ToolStatus
    risk: RiskLevel
    created_at: datetime
    updated_at: datetime


class ToolApproval(BaseModel):
    approved: bool


class ToolValidationResult(BaseModel):
    valid: bool
    detail: str
    tool: ToolRecord


class ToolExecution(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False


class ToolExecutionResult(BaseModel):
    status: Literal["completed", "confirmation_required", "denied", "unavailable", "failed"]
    output: str = ""
    audit_id: str
    risk: RiskLevel


class EvolutionMetrics(BaseModel):
    conversations: int
    providers_configured: int
    tools_created: int
    tools_enabled: int
    tool_executions: int


class EvolutionSnapshot(BaseModel):
    level: int = Field(ge=1, le=5)
    stage: str
    xp: int = Field(ge=0)
    progress: int = Field(ge=0, le=100)
    next_threshold: int | None
    xp_to_next: int = Field(ge=0)
    metrics: EvolutionMetrics


def utc_now() -> datetime:
    return datetime.now(UTC)
