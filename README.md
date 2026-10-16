# GigSense

**A decision simulator for small live-music events: should we host it, what should tickets cost, and what's the downside?**

![Status: Discovery phase](https://img.shields.io/badge/status-discovery%20phase-orange)

> Discovery-stage project. The calculator below is built, but the problem and demand are **not yet validated**: interviews, competitor research and a real-event pilot are still ahead. Claims about demand, accuracy or impact will be added only when evidence exists.

## Problem hypothesis

College committees, cafe owners and small-venue organisers often commit money to artist fees, venue hire and sound before they know how many people will turn up. A weak turnout can leave a loss that is hard to absorb.

**Hypothesis to test:** organisers would benefit from comparing event economics and downside scenarios *before* committing funds.

## What GigSense does today (v0.1)

The organiser enters a plan (capacity, ticket price, fixed costs, optional per-attendee cost and sponsorship, optional low/expected/high turnout) and sees the financial consequences, with every step of the calculation visible.

```
break-even tickets = ceil((fixed costs - sponsorship) / (ticket price - per-attendee cost))
```

**Worked example (illustrative numbers, not real event data):**

| | Plan A: 100-seat venue | Plan B: 200-seat venue |
|---|---|---|
| Fixed costs (venue + artist + sound) | ₹32,000 | ₹40,000 |
| Sponsorship | ₹10,000 | ₹10,000 |
| Ticket price | ₹400 | ₹300 |
| **Break-even tickets** | **55** (55% of capacity) | **100** (50% of capacity) |
| Result if only 40 tickets sell | loss of ₹6,000 | loss of ₹18,000 |

Plan B breaks even at a lower share of its venue, but Plan A loses far less if turnout is poor. Which is "safer" depends on how confident the organiser is in turnout, and that trade-off is what the tool surfaces. The same example is covered by the test suite.

**Features**

- Break-even calculator with fixed vs per-attendee costs and input validation
- Clear message when break-even is unreachable or exceeds venue capacity
- Side-by-side comparison of two plans, including the trade-off between break-even and downside
- Low / expected / high turnout scenarios (organiser-entered assumptions, **not** ML predictions)
- "Show the calculation" and "Assumptions" for every result; cautious wording, not financial advice

**Deliberately not included yet:** attendance forecasting and demand testing. Those only make sense once there is real, permissioned data.

## Run it locally

```bash
git clone https://github.com/boutsoniya/GigSense1.git
cd GigSense1
pip install -r requirements.txt
python -m uvicorn gigsense.api:app --reload
# open http://127.0.0.1:8000
```

Run the tests with `python -m pytest`. API docs are at `/docs` while the server is running.

| Endpoint | Purpose |
|---|---|
| `POST /api/evaluate` | Break-even and scenarios for one plan |
| `POST /api/compare` | Two plans side by side, with observations |
| `GET /api/health` | Health check |

## What I'm trying to learn

Assumptions are tracked separately from findings. This table will be updated with evidence as research happens.

| Assumption | Status | Evidence |
|---|---|---|
| Organisers find it hard to estimate break-even and turnout | Untested | None yet |
| Spreadsheets or gut feel are the main tools today | Untested | None yet |
| A scenario tool would change or clarify a real decision | Untested | None yet |
| Someone would use it again (or pay for it) | Untested | None yet |

Statuses: **Untested**, **Supported**, **Contradicted**. Each change will link to interview notes.

## Research plan and decision criteria

- Interview **8-12 organisers** (college fest committees, cafe/venue owners, independent artists). Script: [`docs/interview_script.md`](docs/interview_script.md)
- Review existing tools and spreadsheet workflows
- Collect figures from **5-10 past events**, with permission ([template](data/past_events_template.csv), [notes](data/README.md))
- Test the calculator with organisers, then pilot on one real event if an organiser agrees

**I will rethink the problem or target group if**, for example, fewer than 4 of 10 organisers report a real loss or a turnout surprise, or if existing spreadsheets already meet their needs. (Thresholds are my starting guess and may be refined.)

## Status

| Workstream | Status |
|---|---|
| Problem hypothesis and scope | Drafted |
| Break-even + scenario calculator (v0.1) | Built; not yet tested with real organisers |
| User interviews (8-12) | Not started |
| Competitor / alternatives review | Not started |
| Past-event data (5-10 events) | Not collected |
| Real-event pilot | Not started |
| Case study | Not written |

## Project structure

```
gigsense/model.py   core maths (no dependencies): break-even, scenarios, comparison, validation
gigsense/api.py     FastAPI endpoints and static page
web/index.html      single-page UI (no build step)
tests/              model and API tests
docs/               interview script
data/               past-event CSV template
```

## Limitations

- The problem and demand are not yet established.
- Organiser estimates may be incomplete or inaccurate, and the tool trusts what it's given.
- The model assumes every ticket sells at one price, with no discounts, refunds, fees or taxes.
- Event economics vary by venue, city, genre and format; college-event findings may not generalise.
- Existing tools may already be enough for some organisers.

## Author

Built and maintained by **Soniya** (`@boutsoniya`). This is an early-stage project: the calculations are transparent, and demand has not yet been validated with real organisers. A case study will be linked here once there is evidence to share.
