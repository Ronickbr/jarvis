import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from .evolution import EvolutionCounts, calculate_evolution
from .policy import classify_tool
from .schemas import EvolutionSnapshot, RiskLevel, ToolCreate, ToolRecord, ToolStatus, utc_now


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS tools (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    language TEXT NOT NULL,
                    code TEXT NOT NULL,
                    input_schema TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    event TEXT NOT NULL,
                    tool_id TEXT,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def create_tool(self, data: ToolCreate) -> ToolRecord:
        now = utc_now()
        record = ToolRecord(
            id=str(uuid.uuid4()),
            **data.model_dump(),
            status=ToolStatus.draft,
            risk=classify_tool(data),
            created_at=now,
            updated_at=now,
        )
        with self._connect() as db:
            db.execute(
                """INSERT INTO tools VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.id,
                    record.name,
                    record.description,
                    record.language,
                    record.code,
                    json.dumps(record.input_schema),
                    json.dumps(record.permissions),
                    record.status.value,
                    record.risk.value,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                ),
            )
        self.audit("tool.created", record.id, {"risk": record.risk.value})
        return record

    def list_tools(self) -> list[ToolRecord]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM tools ORDER BY created_at DESC").fetchall()
        return [self._to_tool(row) for row in rows]

    def get_tool(self, tool_id: str) -> ToolRecord | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tools WHERE id = ?", (tool_id,)).fetchone()
        return self._to_tool(row) if row else None

    def set_status(self, tool_id: str, status: ToolStatus) -> ToolRecord | None:
        with self._connect() as db:
            db.execute(
                "UPDATE tools SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, utc_now().isoformat(), tool_id),
            )
        self.audit("tool.status_changed", tool_id, {"status": status.value})
        return self.get_tool(tool_id)

    def audit(self, event: str, tool_id: str | None, detail: dict[str, Any]) -> str:
        audit_id = str(uuid.uuid4())
        with self._connect() as db:
            db.execute(
                "INSERT INTO audit_log VALUES (?, ?, ?, ?, ?)",
                (audit_id, event, tool_id, json.dumps(detail), utc_now().isoformat()),
            )
        return audit_id

    def evolution(self, configured_providers: int) -> EvolutionSnapshot:
        with self._connect() as db:
            event_rows = db.execute(
                """
                SELECT
                    event,
                    CASE
                        WHEN event IN ('tool.created', 'tool.validation_passed', 'tool.approved')
                        THEN COUNT(DISTINCT tool_id)
                        ELSE COUNT(*)
                    END AS total
                FROM audit_log
                GROUP BY event
                """
            ).fetchall()
            tool_row = db.execute(
                """
                SELECT
                    COUNT(*) AS created,
                    SUM(CASE WHEN status IN ('approved', 'enabled') THEN 1 ELSE 0 END) AS enabled
                FROM tools
                """
            ).fetchone()
        counts = EvolutionCounts(
            events={row["event"]: row["total"] for row in event_rows},
            tools_created=tool_row["created"],
            tools_enabled=tool_row["enabled"] or 0,
        )
        return calculate_evolution(counts, configured_providers)

    @staticmethod
    def _to_tool(row: sqlite3.Row) -> ToolRecord:
        return ToolRecord(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            language=row["language"],
            code=row["code"],
            input_schema=json.loads(row["input_schema"]),
            permissions=json.loads(row["permissions"]),
            status=ToolStatus(row["status"]),
            risk=RiskLevel(row["risk"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
