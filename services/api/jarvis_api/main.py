import sqlite3
import subprocess
from functools import lru_cache
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import Settings, get_settings
from .policy import requires_confirmation, validate_source
from .providers import complete, configured_providers, demo_response
from .routing import PROVIDER_MODELS, choose_route
from .sandbox import SandboxFailure, SandboxUnavailable, execute_in_docker
from .schemas import (
    ChatRequest,
    ChatResponse,
    EvolutionSnapshot,
    ProviderStatus,
    ToolApproval,
    ToolCreate,
    ToolExecution,
    ToolExecutionResult,
    ToolRecord,
    ToolStatus,
    ToolValidationResult,
)
from .storage import Store


@lru_cache
def get_store() -> Store:
    return Store(get_settings().database_path)


SettingsDependency = Annotated[Settings, Depends(get_settings)]
StoreDependency = Annotated[Store, Depends(get_store)]


app = FastAPI(
    title="Jarvis API",
    version=__version__,
    description="Orquestrador local multi-LLM com ferramentas permissionadas.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/v1/health")
def health(settings: SettingsDependency) -> dict[str, object]:
    return {"status": "ok", "version": __version__, "environment": settings.env}


@app.get("/api/v1/evolution", response_model=EvolutionSnapshot)
def evolution(settings: SettingsDependency, store: StoreDependency) -> EvolutionSnapshot:
    return store.evolution(len(configured_providers(settings)))


@app.get("/api/v1/providers", response_model=list[ProviderStatus])
def providers(settings: SettingsDependency) -> list[ProviderStatus]:
    available = configured_providers(settings)
    return [
        ProviderStatus(name=name, configured=name in available, models=models)
        for name, models in PROVIDER_MODELS.items()
    ]


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, settings: SettingsDependency, store: StoreDependency
) -> ChatResponse:
    user_text = next(
        (message.content for message in reversed(request.messages) if message.role == "user"), ""
    )
    available = configured_providers(settings)
    route = choose_route(
        request.provider,
        user_text,
        available,
        request.model,
    )
    if route is None:
        if request.provider.value != "auto":
            raise HTTPException(
                status_code=409, detail="O provedor solicitado não está configurado."
            )
        response = demo_response(user_text)
        store.audit("chat.demo_completed", None, {"model": response.model})
        return response

    failures: list[str] = []
    while route:
        try:
            response = await complete(route, request.messages, settings, request.personality)
            if failures:
                response.reason += f"; fallback após falha em {', '.join(failures)}"
            store.audit(
                "chat.completed",
                None,
                {
                    "provider": response.provider,
                    "model": response.model,
                    "latency_ms": response.latency_ms,
                    "fallbacks": failures,
                },
            )
            return response
        except httpx.HTTPError as error:
            failures.append(route.provider)
            if request.provider.value != "auto":
                raise HTTPException(
                    status_code=502, detail=f"Falha no provedor {route.provider}."
                ) from error
            available.discard(route.provider)
            route = choose_route(request.provider, user_text, available, request.model)

    raise HTTPException(
        status_code=502,
        detail=f"Todos os provedores configurados falharam: {', '.join(failures)}.",
    )


@app.get("/api/v1/tools", response_model=list[ToolRecord])
def list_tools(store: StoreDependency) -> list[ToolRecord]:
    return store.list_tools()


@app.post("/api/v1/tools", response_model=ToolRecord, status_code=201)
def create_tool(payload: ToolCreate, store: StoreDependency) -> ToolRecord:
    try:
        return store.create_tool(payload)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Já existe uma tool com esse nome.") from error


@app.post("/api/v1/tools/{tool_id}/approve", response_model=ToolRecord)
def approve_tool(
    tool_id: str, payload: ToolApproval, store: StoreDependency
) -> ToolRecord:
    current = store.get_tool(tool_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Tool não encontrada.")
    if payload.approved and current.status != ToolStatus.validated:
        raise HTTPException(status_code=409, detail="Valide a tool antes de aprová-la.")
    status = ToolStatus.approved if payload.approved else ToolStatus.disabled
    updated = store.set_status(tool_id, status)
    if payload.approved:
        store.audit("tool.approved", tool_id, {"risk": current.risk.value})
    return updated  # type: ignore[return-value]


@app.post("/api/v1/tools/{tool_id}/validate", response_model=ToolValidationResult)
def validate_tool(tool_id: str, store: StoreDependency) -> ToolValidationResult:
    tool = store.get_tool(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool não encontrada.")
    valid, detail = validate_source(tool.language, tool.code)
    updated = store.set_status(tool.id, ToolStatus.validated if valid else ToolStatus.draft)
    store.audit("tool.validated", tool.id, {"valid": valid, "detail": detail})
    if valid:
        store.audit("tool.validation_passed", tool.id, {"risk": tool.risk.value})
    return ToolValidationResult(valid=valid, detail=detail, tool=updated)  # type: ignore[arg-type]


@app.post("/api/v1/tools/{tool_id}/execute", response_model=ToolExecutionResult)
def execute_tool(
    tool_id: str, payload: ToolExecution, store: StoreDependency
) -> ToolExecutionResult:
    tool = store.get_tool(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool não encontrada.")
    if tool.status not in {ToolStatus.approved, ToolStatus.enabled}:
        audit_id = store.audit("tool.execution_denied", tool.id, {"status": tool.status.value})
        return ToolExecutionResult(status="denied", audit_id=audit_id, risk=tool.risk)
    if requires_confirmation(tool.risk) and not payload.confirmed:
        audit_id = store.audit("tool.confirmation_required", tool.id, {"risk": tool.risk.value})
        return ToolExecutionResult(
            status="confirmation_required", audit_id=audit_id, risk=tool.risk
        )
    try:
        output = execute_in_docker(tool, payload.arguments)
        audit_id = store.audit("tool.executed", tool.id, {"success": True})
        return ToolExecutionResult(
            status="completed", output=output, audit_id=audit_id, risk=tool.risk
        )
    except SandboxUnavailable as error:
        audit_id = store.audit("tool.sandbox_unavailable", tool.id, {"message": str(error)})
        return ToolExecutionResult(
            status="unavailable", output=str(error), audit_id=audit_id, risk=tool.risk
        )
    except (SandboxFailure, subprocess.TimeoutExpired) as error:
        audit_id = store.audit("tool.execution_failed", tool.id, {"message": str(error)})
        return ToolExecutionResult(
            status="failed", output=str(error), audit_id=audit_id, risk=tool.risk
        )
