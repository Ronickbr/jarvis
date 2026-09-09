from dataclasses import dataclass

from .schemas import EvolutionMetrics, EvolutionSnapshot


STAGES = ("NÚCLEO", "SENCIENTE", "ADAPTATIVO", "COGNITIVO", "ÔMEGA")
THRESHOLDS = (0, 100, 250, 500, 900)
EVENT_POINTS = {
    "chat.demo_completed": 3,
    "chat.completed": 8,
    "tool.created": 10,
    "tool.validated": 15,
    "tool.status_changed": 20,
    "tool.executed": 25,
}


@dataclass(frozen=True)
class EvolutionCounts:
    events: dict[str, int]
    tools_created: int
    tools_enabled: int


def calculate_evolution(counts: EvolutionCounts, configured_providers: int) -> EvolutionSnapshot:
    xp = configured_providers * 20
    xp += sum(EVENT_POINTS.get(event, 0) * count for event, count in counts.events.items())
    level = max(index + 1 for index, threshold in enumerate(THRESHOLDS) if xp >= threshold)
    current_threshold = THRESHOLDS[level - 1]
    next_threshold = THRESHOLDS[level] if level < len(THRESHOLDS) else None
    if next_threshold is None:
        progress = 100
        xp_to_next = 0
    else:
        progress = round((xp - current_threshold) / (next_threshold - current_threshold) * 100)
        xp_to_next = next_threshold - xp
    return EvolutionSnapshot(
        level=level,
        stage=STAGES[level - 1],
        xp=xp,
        progress=max(0, min(100, progress)),
        next_threshold=next_threshold,
        xp_to_next=max(0, xp_to_next),
        metrics=EvolutionMetrics(
            conversations=counts.events.get("chat.completed", 0) + counts.events.get("chat.demo_completed", 0),
            providers_configured=configured_providers,
            tools_created=counts.tools_created,
            tools_enabled=counts.tools_enabled,
            tool_executions=counts.events.get("tool.executed", 0),
        ),
    )
