from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_uses_honest_demo_mode_without_keys(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Olá, Jarvis"}]},
    )
    assert response.status_code == 200
    assert response.json()["demo"] is True
    assert response.json()["provider"] == "demo"


def test_manual_provider_without_key_is_refused(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Olá"}],
            "provider": "openai",
        },
    )
    assert response.status_code == 409


def test_draft_tool_cannot_execute(client: TestClient) -> None:
    created = client.post(
        "/api/v1/tools",
        json={
            "name": "hello_world",
            "description": "Imprime uma saudação simples.",
            "language": "python",
            "code": "print('hello')",
        },
    )
    assert created.status_code == 201
    tool_id = created.json()["id"]

    response = client.post(f"/api/v1/tools/{tool_id}/execute", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "denied"


def test_critical_tool_requires_confirmation_after_approval(client: TestClient) -> None:
    created = client.post(
        "/api/v1/tools",
        json={
            "name": "dangerous_tool",
            "description": "Simula uma operação destrutiva.",
            "language": "python",
            "code": "import os\nos.system('rm -rf /tmp/example')",
        },
    ).json()
    client.post(f"/api/v1/tools/{created['id']}/validate")
    client.post(f"/api/v1/tools/{created['id']}/approve", json={"approved": True})
    response = client.post(f"/api/v1/tools/{created['id']}/execute", json={})
    assert response.json()["status"] == "confirmation_required"
