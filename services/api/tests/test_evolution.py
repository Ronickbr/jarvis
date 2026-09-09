from jarvis_api.evolution import EvolutionCounts, calculate_evolution


def test_evolution_starts_at_core() -> None:
    snapshot = calculate_evolution(
        EvolutionCounts(events={}, tools_created=0, tools_enabled=0),
        configured_providers=0,
    )
    assert snapshot.level == 1
    assert snapshot.stage == "NÚCLEO"
    assert snapshot.progress == 0


def test_only_safe_milestones_increase_evolution() -> None:
    snapshot = calculate_evolution(
        EvolutionCounts(
            events={
                "chat.completed": 5,
                "tool.validation_passed": 1,
                "tool.approved": 1,
                "tool.executed": 1,
                "tool.execution_failed": 99,
                "tool.execution_denied": 99,
            },
            tools_created=1,
            tools_enabled=1,
        ),
        configured_providers=2,
    )
    assert snapshot.xp == 140
    assert snapshot.level == 2
    assert snapshot.stage == "SENCIENTE"
    assert snapshot.metrics.conversations == 5
    assert snapshot.metrics.tool_executions == 1


def test_evolution_api_records_demo_conversation(client) -> None:
    before = client.get("/api/v1/evolution").json()
    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Olá, Jarvis"}]},
    )
    after = client.get("/api/v1/evolution").json()
    assert response.status_code == 200
    assert after["xp"] == before["xp"] + 3
    assert after["metrics"]["conversations"] == before["metrics"]["conversations"] + 1
