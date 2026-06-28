# AskRevenue

**Ask plain-English questions about a subscription business and get charts + answers.**

AskRevenue turns natural language ("what was MRR by month last year?", "which plan
churns most?") into **safe, read-only SQL** over a realistic subscriptions dataset,
then renders the right chart and a plain-English summary. The generated SQL is shown
by default — transparency is the point. Clients distrust black-box text-to-SQL, so
AskRevenue makes every query inspectable and runs it through a least-privilege,
SELECT-only database role.

> **Status:** under active construction. This README grows with each milestone.
> Milestone 1 (scaffold + database + rich seed data) is complete.

---

## What it does

- **Ask view** — a big input, example questions, the generated SQL in a collapsible
  block (shown by default), the chart, and a one-paragraph summary.
- **Dashboards** — save questions, pin charts, and re-run them.
- **Schema explorer** — browse exactly what the AI can query, so viewers trust it.
- **Safety first** — generated SQL is validated to be a single `SELECT`, executed on a
  read-only role, capped, and time-limited. No writes, ever.
- **Demo mode** — seeded data and a curated fallback library mean the app is fully
  clickable with zero setup, even without an Anthropic API key.

## Architecture

```
┌──────────────────────┐        ┌─────────────────────────────┐        ┌──────────────┐
│  Next.js 15 (web)    │  HTTP  │  FastAPI (api)              │  SQL   │  Postgres    │
│  App Router + TS     │ ─────► │                             │ ─────► │              │
│  Tailwind + Recharts │        │  • NL→SQL via Claude        │  R/W   │ star schema  │
│                      │ ◄───── │  • SQL safety validator     │ ◄───── │ + app tables │
│  Ask / Dashboard /   │  JSON  │  • read-only query executor │        │              │
│  Schema explorer     │        │  • saved questions + dash   │  RO    │ askrevenue_ro│
└──────────────────────┘        └─────────────────────────────┘        └──────────────┘
```

- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + Recharts → Vercel.
- **Backend:** FastAPI (Python 3.12, managed with `uv`) → Railway.
- **Database:** Postgres (SQLAlchemy + Alembic migrations) → Railway.
- **Model layer:** Anthropic Claude via the official SDK (`ANTHROPIC_API_KEY`).

### Data model (star-ish schema)

| Table               | Purpose                                                      |
| ------------------- | ----------------------------------------------------------- |
| `dim_customer`      | Customers — segment, country, signup date                   |
| `dim_plan`          | Plans — tier, billing interval, price, normalised MRR       |
| `fact_subscription` | Subscriptions — status, start/end, MRR contribution         |
| `fact_payment`      | Invoices/payments — amount, status, failure reason          |
| `fact_churn`        | Churn events — reason, voluntary flag, MRR lost             |
| `saved_questions`   | App: saved NL questions + SQL + chart config                |
| `dashboards` / `dashboard_items` | App: dashboards and pinned charts              |

The seed runs a month-by-month simulation over ~24 months, so the data tells a
coherent story (growing MRR, tier-dependent churn, realistic payment-failure mix).

## Repo layout

```
askrevenue/
├── api/                 # FastAPI backend (uv, SQLAlchemy, Alembic)
│   ├── app/             # application code (models, seed, config, routers)
│   └── alembic/         # migrations
├── web/                 # Next.js frontend (added in a later milestone)
├── infra/db-init/       # Postgres init SQL (read-only role provisioning)
├── scripts/             # local helpers (non-Docker Postgres fallback)
├── docker-compose.yml   # local Postgres
└── Makefile             # one-command workflows
```

## Run locally

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (for Postgres), or a local Postgres 16.
- [`uv`](https://docs.astral.sh/uv/) for Python.
- Node 18+ for the web app (added later).

### 1. Configure environment

```bash
cp .env.example .env        # defaults work out of the box for local dev
```

`ANTHROPIC_API_KEY` is optional — leave it blank to run in fallback mode (the app
answers from a curated library of example questions instead of calling Claude).

### 2. Start the database and seed it

```bash
make seed     # starts Postgres, runs migrations, grants the read-only role, seeds data
```

This is the one command you need. It is idempotent — re-run it any time to reset the
demo data.

<details>
<summary>No Docker? Use the local-Postgres fallback.</summary>

If you can't pull Docker images, this repo includes a script that runs a throwaway
Postgres 16 cluster using a local install:

```bash
PGDATA=/tmp/askrevenue-pgdata bash scripts/local-pg.sh start
cd api && uv run alembic upgrade head && uv run python -m app.seed
```
</details>

### 3. Run the backend

```bash
make api      # http://localhost:8000  (docs at /docs)
```

Check it's alive:

```bash
curl localhost:8000/health
# {"status":"ok","environment":"development","llm_enabled":false}
```

### Useful Make targets

```bash
make help        # list everything
make db-up       # start Postgres only
make migrate     # apply migrations
make seed        # migrate + seed demo data
make api         # run FastAPI on :8000
make db-reset    # stop Postgres and DELETE all data
```

## Environment variables

| Variable                  | Where      | Description                                            |
| ------------------------- | ---------- | ------------------------------------------------------ |
| `DATABASE_URL`            | api        | Full-privilege connection (migrations, seeding, app)   |
| `READONLY_DATABASE_URL`   | api        | SELECT-only connection for executing generated SQL     |
| `ANTHROPIC_API_KEY`       | api        | Claude API key. Blank → curated fallback mode          |
| `ANTHROPIC_MODEL`         | api        | Claude model id (default `claude-sonnet-4-6`)          |
| `QUERY_ROW_LIMIT`         | api        | Max rows returned by a generated query (default 1000)  |
| `QUERY_TIMEOUT_MS`        | api        | Statement timeout for generated queries (default 5000) |
| `CORS_ORIGINS`            | api        | Comma-separated allowed origins                        |
| `NEXT_PUBLIC_API_BASE_URL`| web        | Base URL the browser uses to reach the API             |

## Deployment

Deploy notes for Vercel (web) + Railway (api + Postgres) are added in the final
milestone.

## Safety model

- Generated SQL is parsed and validated to be a **single `SELECT`** (no DML/DDL, no
  multiple statements, no writes) before it ever runs.
- It executes on a dedicated **read-only Postgres role** (`askrevenue_ro`) that has
  only `SELECT` — defence in depth even if validation were bypassed.
- Results are **row-capped** and **time-limited**.
- The exact SQL is **shown to the user**.
