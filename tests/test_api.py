from fastapi.testclient import TestClient

from gigsense.api import app

client = TestClient(app)

PLAN_A = {
    "name": "Plan A",
    "capacity": 100,
    "ticket_price": 400,
    "fixed_costs": 32000,
    "sponsorship": 10000,
    "turnout": {"low": 40, "expected": 60, "high": 90},
}
PLAN_B = {
    "name": "Plan B",
    "capacity": 200,
    "ticket_price": 300,
    "fixed_costs": 40000,
    "sponsorship": 10000,
    "turnout": {"low": 40, "expected": 90, "high": 150},
}


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_evaluate():
    r = client.post("/api/evaluate", json=PLAN_A)
    assert r.status_code == 200
    body = r.json()
    assert body["break_even_tickets"] == 55
    assert body["scenarios"][0]["profit"] == -6000
    assert body["assumptions"]


def test_compare():
    r = client.post("/api/compare", json={"a": PLAN_A, "b": PLAN_B})
    assert r.status_code == 200
    body = r.json()
    assert body["a"]["break_even_tickets"] == 55
    assert body["b"]["break_even_tickets"] == 100
    assert any("trade off" in o for o in body["observations"])


def test_invalid_field_rejected():
    r = client.post("/api/evaluate", json={**PLAN_A, "capacity": 0})
    assert r.status_code == 422


def test_business_rule_rejected():
    bad = {**PLAN_A, "turnout": {"low": 80, "expected": 60, "high": 90}}
    r = client.post("/api/evaluate", json=bad)
    assert r.status_code == 422
    assert "low <= expected <= high" in r.json()["detail"]


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "GigSense" in r.text
