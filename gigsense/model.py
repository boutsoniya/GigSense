"""Core break-even and scenario maths for GigSense.

Everything in this module is plain arithmetic on organiser-entered inputs.
Nothing is predicted or learned from data, and every output is only as good as
the numbers that were typed in. Turnout scenarios are assumptions, not forecasts.

Break-even formula:

    break-even tickets = ceil((fixed costs - sponsorship) / (ticket price - per-attendee cost))
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional


def fmt(x: float) -> str:
    """Format a number without trailing zeros, with thousands separators."""
    return f"{x:,.2f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TurnoutScenarios:
    """Organiser-entered attendance assumptions (paid tickets)."""

    low: int
    expected: int
    high: int


@dataclass(frozen=True)
class EventPlan:
    """One event plan. Amounts are in a single currency chosen by the organiser."""

    name: str
    capacity: int
    ticket_price: float
    fixed_costs: float
    per_attendee_cost: float = 0.0
    sponsorship: float = 0.0
    turnout: Optional[TurnoutScenarios] = None

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise ValueError("capacity must be at least 1")
        for label in ("ticket_price", "fixed_costs", "per_attendee_cost", "sponsorship"):
            if getattr(self, label) < 0:
                raise ValueError(f"{label} cannot be negative")
        if self.turnout is not None:
            t = self.turnout
            if min(t.low, t.expected, t.high) < 0:
                raise ValueError("turnout values cannot be negative")
            if not (t.low <= t.expected <= t.high):
                raise ValueError("turnout must satisfy low <= expected <= high")
            if t.high > self.capacity:
                raise ValueError("turnout cannot exceed venue capacity")


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------


def margin_per_ticket(plan: EventPlan) -> float:
    return plan.ticket_price - plan.per_attendee_cost


def break_even_tickets(plan: EventPlan) -> Optional[int]:
    """Paid tickets needed to cover costs.

    Returns 0 if sponsorship already covers fixed costs, and None if each
    ticket brings in no more than it costs to serve (break-even is unreachable
    from ticket sales).
    """
    net = plan.fixed_costs - plan.sponsorship
    if net <= 0:
        return 0
    margin = margin_per_ticket(plan)
    if margin <= 0:
        return None
    # round() guards against floating-point noise such as 55.00000000001
    return math.ceil(round(net / margin, 9))


def profit_at(plan: EventPlan, attendance: int) -> float:
    """Profit (negative = loss) if `attendance` paid tickets are sold."""
    if attendance < 0:
        raise ValueError("attendance cannot be negative")
    if attendance > plan.capacity:
        raise ValueError("attendance cannot exceed venue capacity")
    return attendance * margin_per_ticket(plan) - plan.fixed_costs + plan.sponsorship


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass
class ScenarioResult:
    label: str
    attendance: int
    profit: float


@dataclass
class Evaluation:
    name: str
    capacity: int
    break_even_tickets: Optional[int]
    break_even_share_of_capacity: Optional[float]
    achievable_within_capacity: bool
    net_to_recover_from_tickets: float
    margin_per_ticket: float
    upfront_cash: float
    max_profit_at_capacity: float
    scenarios: List[ScenarioResult] = field(default_factory=list)
    calculation: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)


@dataclass
class Comparison:
    a: Evaluation
    b: Evaluation
    observations: List[str] = field(default_factory=list)


ASSUMPTIONS = [
    "All amounts are the numbers the organiser entered; nothing is verified.",
    "Fixed costs are treated as paid upfront and sponsorship as received in full.",
    "Every paid ticket sells at the entered price (no discounts, refunds, fees or taxes).",
    "Turnout scenarios are organiser assumptions, not predictions.",
    "This is a planning aid, not financial advice.",
]


def _money(x: float) -> str:
    return fmt(abs(x))


def evaluate(plan: EventPlan) -> Evaluation:
    be = break_even_tickets(plan)
    net = plan.fixed_costs - plan.sponsorship
    margin = margin_per_ticket(plan)
    achievable = be is not None and be <= plan.capacity
    share = (be / plan.capacity) if be is not None else None

    calculation = [
        f"Fixed costs: {fmt(plan.fixed_costs)}",
        f"Sponsorship: {fmt(plan.sponsorship)}",
        f"Amount to recover from tickets: {fmt(plan.fixed_costs)} - {fmt(plan.sponsorship)} = {fmt(net)}",
        f"Margin per ticket: {fmt(plan.ticket_price)} - {fmt(plan.per_attendee_cost)} = {fmt(margin)}",
    ]
    if net <= 0:
        calculation.append("Break-even tickets: 0 (sponsorship covers fixed costs)")
    elif margin <= 0:
        calculation.append("Break-even tickets: not reachable (margin per ticket is zero or negative)")
    else:
        calculation.append(
            f"Break-even tickets: ceil({fmt(net)} / {fmt(margin)}) = {be}"
        )

    notes: List[str] = []
    if be == 0:
        notes.append(
            "On the entered numbers, sponsorship already covers fixed costs; ticket sales add to profit."
        )
    elif be is None:
        notes.append(
            "Each ticket brings in no more than it costs to serve, so ticket sales alone cannot cover "
            "fixed costs. Review the ticket price or per-attendee costs."
        )
    elif not achievable:
        notes.append(
            f"Break-even needs {be} paid tickets but capacity is {plan.capacity}. "
            "On these inputs the event cannot break even; review costs, price, venue size or sponsorship."
        )
    else:
        notes.append(
            f"Break-even needs {be} paid tickets ({share:.0%} of capacity)."
        )
        if share is not None and share > 0.8:
            notes.append(
                "That leaves little room for a turnout shortfall; consider how confident you are in turnout."
            )

    scenarios: List[ScenarioResult] = []
    if plan.turnout is not None:
        t = plan.turnout
        for label, n in (("low", t.low), ("expected", t.expected), ("high", t.high)):
            scenarios.append(ScenarioResult(label, n, profit_at(plan, n)))
        for s in scenarios:
            verb = "profit" if s.profit >= 0 else "loss"
            notes.append(
                f"At {s.label} turnout ({s.attendance} tickets) the result is a {verb} of {_money(s.profit)}."
            )
        if be is not None and t.expected < be:
            notes.append(
                "Expected turnout is below break-even on the entered numbers; review costs before proceeding."
            )
        elif be is None:
            notes.append(
                "Expected turnout cannot reach break-even because margin per ticket is not positive."
            )

    return Evaluation(
        name=plan.name,
        capacity=plan.capacity,
        break_even_tickets=be,
        break_even_share_of_capacity=share,
        achievable_within_capacity=achievable,
        net_to_recover_from_tickets=net,
        margin_per_ticket=margin,
        upfront_cash=plan.fixed_costs,
        max_profit_at_capacity=profit_at(plan, plan.capacity),
        scenarios=scenarios,
        calculation=calculation,
        notes=notes,
        assumptions=list(ASSUMPTIONS),
    )


def _low_profit(e: Evaluation) -> Optional[float]:
    for s in e.scenarios:
        if s.label == "low":
            return s.profit
    return None


def compare(plan_a: EventPlan, plan_b: EventPlan) -> Comparison:
    a, b = evaluate(plan_a), evaluate(plan_b)
    obs: List[str] = []

    both_reachable = a.achievable_within_capacity and b.achievable_within_capacity
    if both_reachable:
        sa, sb = a.break_even_share_of_capacity, b.break_even_share_of_capacity
        if abs(sa - sb) < 1e-9:
            obs.append(f"Both plans break even at {sa:.0%} of capacity.")
        else:
            lower, hi = (a, b) if sa < sb else (b, a)
            obs.append(
                f"{lower.name} breaks even at a lower share of capacity "
                f"({lower.break_even_share_of_capacity:.0%} vs {hi.break_even_share_of_capacity:.0%})."
            )
    else:
        for e in (a, b):
            if not e.achievable_within_capacity:
                obs.append(f"{e.name} cannot break even within its venue capacity on these inputs.")

    la, lb = _low_profit(a), _low_profit(b)
    if la is not None and lb is not None:
        if abs(la - lb) < 1e-9:
            obs.append("Both plans have the same result at low turnout.")
        else:
            better, worse, bp, wp = (a, b, la, lb) if la > lb else (b, a, lb, la)
            obs.append(
                f"At low turnout, {better.name} does better "
                f"({'profit' if bp >= 0 else 'loss'} of {_money(bp)} vs "
                f"{'profit' if wp >= 0 else 'loss'} of {_money(wp)})."
            )

    if a.max_profit_at_capacity != b.max_profit_at_capacity:
        top = a if a.max_profit_at_capacity > b.max_profit_at_capacity else b
        obs.append(
            f"{top.name} has the higher best case (a sell-out result of {fmt(top.max_profit_at_capacity)})."
        )

    # Trade-off line when the plans disagree on risk vs. upside.
    if both_reachable and la is not None and lb is not None:
        lower_be = a if a.break_even_share_of_capacity < b.break_even_share_of_capacity else b
        safer_low = a if la > lb else b
        if (
            abs(a.break_even_share_of_capacity - b.break_even_share_of_capacity) > 1e-9
            and abs(la - lb) > 1e-9
            and lower_be is not safer_low
        ):
            obs.append(
                f"The plans trade off: {lower_be.name} needs a smaller share of its venue to break even, "
                f"while {safer_low.name} loses less if turnout is poor. Which is safer depends on how "
                "confident you are in turnout."
            )

    return Comparison(a=a, b=b, observations=obs)
