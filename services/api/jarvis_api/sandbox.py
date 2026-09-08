import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .schemas import ToolRecord


class SandboxUnavailable(RuntimeError):
    pass


class SandboxFailure(RuntimeError):
    pass


def execute_in_docker(tool: ToolRecord, arguments: dict[str, object]) -> str:
    if shutil.which("docker") is None:
        raise SandboxUnavailable(
            "Docker não está instalado; execução local insegura foi recusada."
        )

    image = "python:3.12-alpine" if tool.language == "python" else "node:22-alpine"
    filename = "tool.py" if tool.language == "python" else "tool.js"
    command = (
        ["python", f"/workspace/{filename}"]
        if tool.language == "python"
        else ["node", f"/workspace/{filename}"]
    )

    with tempfile.TemporaryDirectory(prefix="jarvis-tool-") as directory:
        workdir = Path(directory)
        (workdir / filename).write_text(tool.code, encoding="utf-8")
        (workdir / "input.json").write_text(json.dumps(arguments), encoding="utf-8")
        process = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--memory",
                "256m",
                "--cpus",
                "0.5",
                "--pids-limit",
                "64",
                "--mount",
                f"type=bind,src={workdir},dst=/workspace,readonly",
                image,
                *command,
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    output = (process.stdout + process.stderr).strip()
    if process.returncode != 0:
        raise SandboxFailure(output[:8000] or f"Processo terminou com código {process.returncode}")
    return output[:8000]
