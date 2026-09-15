import json
import logging
import time
import uuid

from app.safety import redact


class AuditLogger:
    """Persist only redacted operational metadata, never raw user text."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("banking_agent")

    def trace_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def event(self, trace_id: str, stage: str, outcome: str, started: float, **metadata: object) -> None:
        payload = {
            "trace_id": trace_id,
            "stage": stage,
            "outcome": outcome,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "metadata": {key: redact(str(value)) for key, value in metadata.items()},
        }
        self.logger.info(json.dumps(payload, sort_keys=True))
