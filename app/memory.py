from dataclasses import dataclass, field


@dataclass
class SessionMemory:
    """Short-term, non-PII memory. It is explicitly resettable and bounded."""

    max_items: int = 6
    items: list[str] = field(default_factory=list)

    def add(self, fact: str) -> None:
        if fact and len(fact) <= 160:
            self.items.append(fact)
            del self.items[:-self.max_items]

    def context(self) -> list[str]:
        return list(self.items)

    def reset(self) -> None:
        self.items.clear()
