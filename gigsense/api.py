"""FastAPI app: JSON endpoints around the model, plus the static web page."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .model import EventPlan, TurnoutScenarios, compare, evaluate

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(
    title="GigSense",
    version=__version__,
    description="Transparent break-even and scenario calculator for small live-music events.",
)


class TurnoutIn(BaseModel):
    low: int = Field(ge=0, allow_inf_nan=False)
    expected: int = Field(ge=0, allow_inf_nan=False)
    high: int = Field(ge=0, allow_inf_nan=False)


class PlanIn(BaseModel):
    name: str = Field(default="Plan", max_length=60)
    capacity: int = Field(ge=1)
    ticket_price: float = Field(ge=0, allow_inf_nan=False)
    fixed_costs: float = Field(ge=0, allow_inf_nan=False)
    per_attendee_cost: float = Field(default=0, ge=0, allow_inf_nan=False)
    sponsorship: float = Field(default=0, ge=0)
    turnout: Optional[TurnoutIn] = None

    def to_plan(self) -> EventPlan:
        turnout = TurnoutScenarios(**self.turnout.model_dump()) if self.turnout else None
        try:
            return EventPlan(
                name=self.name.strip() or "Plan",
                capacity=self.capacity,
                ticket_price=self.ticket_price,
                fixed_costs=self.fixed_costs,
                per_attendee_cost=self.per_attendee_cost,
                sponsorship=self.sponsorship,
                turnout=turnout,
            )
        except ValueError as exc:  # business-rule validation from the model
            raise HTTPException(status_code=422, detail=str(exc)) from exc


class CompareIn(BaseModel):
    a: PlanIn
    b: PlanIn


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/api/evaluate")
def evaluate_plan(plan: PlanIn) -> dict:
    return asdict(evaluate(plan.to_plan()))


@app.post("/api/compare")
def compare_plans(body: CompareIn) -> dict:
    return asdict(compare(body.a.to_plan(), body.b.to_plan()))


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
