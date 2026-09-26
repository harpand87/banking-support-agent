from dataclasses import dataclass, field

from app.safety import detect_pii


@dataclass
class SessionMemory:
    """Short-term, non-PII memory. It is explicitly resettable and bounded."""

    max_items: int = 6
    items: list[str] = field(default_factory=list)
    workflow_steps: list[str] = field(default_factory=list)
    workflow_index: int = 0

    def __post_init__(self) -> None:
        if self.max_items < 1:
            raise ValueError("max_items must be positive")

    def add(self, fact: str) -> None:
        if fact and len(fact) <= 160 and not detect_pii(fact):
            self.items.append(fact)
            del self.items[:-self.max_items]

    def context(self) -> list[str]:
        return list(self.items)

    def remember_workflow(self, steps: list[str]) -> None:
        self.workflow_steps = [step[:160] for step in steps[:6] if not detect_pii(step)]
        self.workflow_index = 0

    def next_workflow_step(self, advance: bool = False) -> str | None:
        if advance and self.workflow_index < len(self.workflow_steps):
            self.workflow_index += 1
        if self.workflow_index >= len(self.workflow_steps):
            return None
        return self.workflow_steps[self.workflow_index]

    def reset(self) -> None:
        self.items.clear()
        self.workflow_steps.clear()
        self.workflow_index = 0
