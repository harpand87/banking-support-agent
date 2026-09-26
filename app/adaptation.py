from dataclasses import dataclass


@dataclass
class FeedbackProfile:
    style: str = "balanced"
    feedback_count: int = 0
    helpful_count: int = 0
    unhelpful_count: int = 0
    style_change_count: int = 0

    def apply(self, helpful: bool, reason: str = "") -> None:
        self.feedback_count += 1
        if helpful:
            self.helpful_count += 1
            return
        self.unhelpful_count += 1
        previous_style = self.style
        if "long" in reason.lower():
            self.style = "concise"
        elif "detail" in reason.lower():
            self.style = "detailed"
        if self.style != previous_style:
            self.style_change_count += 1

    def metrics(self) -> dict[str, int | str | float]:
        return {
            "style": self.style,
            "feedback_count": self.feedback_count,
            "helpful_count": self.helpful_count,
            "unhelpful_count": self.unhelpful_count,
            "style_change_count": self.style_change_count,
            "helpful_rate": self.helpful_count / self.feedback_count if self.feedback_count else 0.0,
        }
