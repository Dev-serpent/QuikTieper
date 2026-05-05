from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from CamComs.paths import DEFAULT_CAMCOMS_DIR


DEFAULT_AUDIT_LOG_PATH = DEFAULT_CAMCOMS_DIR / "audit.log"


class AuditLog:
    def __init__(self, path: Path = DEFAULT_AUDIT_LOG_PATH) -> None:
        self.path = path

    def record(self, event: dict[str, Any]) -> None:
        payload = {
            "timestamp": int(time.time()),
            **event,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")

    def read_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        return [json.loads(line) for line in lines[-limit:] if line.strip()]
