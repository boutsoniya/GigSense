import pytest

from gigsense import EventPlan, TurnoutScenarios, break_even_tickets, compare, evaluate, profit_at

# The illustrative example from the README (made-up numbers, not real event data).
PLAN_A = EventPlan(
    name="Plan A",
    capacity=100,
    ticket_price=400,
    fixed_costs=32_000,
    sponsorship=10_000,
    turnout=TurnoutScenarios(low=40, expected=60, high=90),
)
PLAN_B = EventPlan(
    name="Plan B",
    capacity=200,
    ticket_price=300,
    fixed_costs=40_000,
    sponsorship=10_000,
    turnout=TurnoutScenarios(low=40, expected=90, high=150),
)


def test_readme_example_break_even():
    assert break_even_tickets(PLAN_A) == 55
    assert break_even_tickets(PLAN_B) == 100


def test_readme_example_loss_at_40_tickets():
    assert profit_at(PLAN_A, 40) == -6_000
    assert profit_at(PLAN_B, 40) == -18_000


def test_break_even_rounds_up():
    plan = EventPlan("x", capacity=50, ticket_price=300, fixed_costs=1_000)
    assert break_even_tickets(plan) == 4  # 3.33 -> 4


def test_per_attendee_cost_reduces_margin():
    plan = EventPlan("x", capacity=500, ticket_price=300, fixed_costs=10_000, per_attendee_cost=100)
    assert break_even_tickets(plan) == 50  # 10000 / 200


def test_sponsorship_can_cover_fixed_costs():
    plan = EventPlan("x", capacity=100, ticket_price=200, fixed_costs=5_000, sponsorship=6_000)
    assert break_even_tickets(plan) == 0
    assert evaluate(plan).achievable_within_capacity is True


def test_unreachable_when_margin_not_positive():
    plan = EventPlan("x", capacity=100, ticket_price=100, fixed_costs=5_000, per_attendee_cost=100)
    ev = evaluate(plan)
    assert break_even_tickets(plan) is None
    assert ev.achievable_within_capacity is False
    assert ev.break_even_share_of_capacity is None
    assert any("cannot cover" in n for n in ev.notes)


def test_not_achievable_when_break_even_exceeds_capacity():
    plan = EventPlan("x", capacity=50, ticket_price=100, fixed_costs=10_000)
    ev = evaluate(plan)
    assert ev.break_even_tickets == 100
    assert ev.achievable_within_capacity is False
    assert any("cannot break even" in n for n in ev.notes)


def test_scenarios_and_cautious_language():
    ev = evaluate(PLAN_A)
    labels = [s.label for s in ev.scenarios]
    assert labels == ["low", "expected", "high"]
    assert ev.scenarios[0].profit == -6_000
    text = " ".join(ev.notes).lower()
    assert "guarantee" not in text
    assert "loss of 6,000" in text


def test_expected_below_break_even_triggers_review_note():
    plan = EventPlan(
        "x", capacity=100, ticket_price=400, fixed_costs=32_000, sponsorship=10_000,
        turnout=TurnoutScenarios(low=20, expected=30, high=60),
    )
    assert any("review costs before proceeding" in n for n in evaluate(plan).notes)


def test_calculation_steps_are_exposed():
    steps = evaluate(PLAN_A).calculation
    assert any("ceil(22,000 / 400) = 55" in s for s in steps)


def test_compare_surfaces_trade_off():
    cmp = compare(PLAN_A, PLAN_B)
    joined = " ".join(cmp.observations)
    assert "Plan B breaks even at a lower share of capacity" in joined
    assert "At low turnout, Plan A does better" in joined
    assert "trade off" in joined


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(capacity=0, ticket_price=100, fixed_costs=0),
        dict(capacity=10, ticket_price=-1, fixed_costs=0),
        dict(capacity=10, ticket_price=100, fixed_costs=-5),
        dict(capacity=10, ticket_price=100, fixed_costs=0, sponsorship=-1),
        dict(capacity=10, ticket_price=100, fixed_costs=0, per_attendee_cost=-1),
        dict(capacity=10, ticket_price=100, fixed_costs=0, turnout=TurnoutScenarios(5, 3, 8)),
        dict(capacity=10, ticket_price=100, fixed_costs=0, turnout=TurnoutScenarios(1, 5, 11)),
        dict(capacity=10, ticket_price=100, fixed_costs=0, turnout=TurnoutScenarios(-1, 5, 8)),
    ],
)
def test_invalid_inputs_rejected(kwargs):
    with pytest.raises(ValueError):
        EventPlan(name="bad", **kwargs)


def test_profit_at_rejects_out_of_range_attendance():
    with pytest.raises(ValueError):
        profit_at(PLAN_A, 101)
    with pytest.raises(ValueError):
        profit_at(PLAN_A, -1)


@pytest.mark.parametrize(
    "field,value",
    [
        ("ticket_price", float("nan")),
        ("fixed_costs", float("inf")),
        ("per_attendee_cost", float("-inf")),
        ("sponsorship", float("nan")),
    ],
)
def test_non_finite_money_values_are_rejected(field, value):
    kwargs = dict(name="x", capacity=10, ticket_price=100, fixed_costs=100)
    kwargs[field] = value
    with pytest.raises(ValueError, match="finite number"):
        EventPlan(**kwargs)
