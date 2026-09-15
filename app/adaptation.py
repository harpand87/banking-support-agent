from dataclasses import dataclass


@dataclass
class FeedbackProfile:
    style: str = "balanced"
    feedback_count: int = 0

    def apply(self, helpful: bool, reason: str = "") -> None:
        self.feedback_count += 1
        if helpful:
            return
        if "long" in reason.lower():
            self.style = "concise"
        elif "detail" in reason.lower():
            self.style = "detailed"
