"""GigSense: a transparent break-even and scenario calculator for small live-music events."""

from .model import (
    Comparison,
    EventPlan,
    Evaluation,
    ScenarioResult,
    TurnoutScenarios,
    break_even_tickets,
    compare,
    evaluate,
    profit_at,
)

__all__ = [
    "Comparison",
    "EventPlan",
    "Evaluation",
    "ScenarioResult",
    "TurnoutScenarios",
    "break_even_tickets",
    "compare",
    "evaluate",
    "profit_at",
]

__version__ = "0.1.0"
