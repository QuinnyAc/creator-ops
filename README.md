# Creator Ops

> An open-source creator operations workspace — from idea to insight.

Creator Ops helps individual creators and small content teams manage the full content production loop in one place:

**Inspiration → Topic → Content → Publication → Metrics → Review → Insight → Better next topic**

It is intentionally not another generic Notion-style database. Creator Ops understands the domain relationship between a topic, a reusable content asset, each platform-specific publication, its time-series metrics, the review produced from those results, and the reusable creator knowledge that should influence the next decision.

## Why Creator Ops

Generic databases are excellent at storing rows. Creator Ops is opinionated about the creator workflow:

- capture an idea with almost no friction;
- decide whether the topic is worth making before production starts;
- manage the content lifecycle instead of a generic task lifecycle;
- separate reusable `Content` from each platform-specific `Publication`;
- preserve metric snapshots instead of overwriting yesterday's numbers;
- compare Content Pillars, platforms, title patterns, and recent interest changes;
- turn a one-off review into a reusable Creator Playbook insight.

## Current MVP

The repository includes a working end-to-end product foundation for:

- low-friction Inspiration Inbox with conversion into Topics;
- searchable Topic Library with weighted opportunity / priority scoring;
- Content Pillars and tags for stable strategy + flexible taxonomy;
- content production Kanban and per-content workspace;
- multi-platform creator accounts and publication management;
- monthly publishing calendar;
- manual metric snapshots and 24h / 72h / 7d / 30d milestones;
- bulk CSV metric import with idempotent snapshot upserts;
- CSV exports for topics, content, publications, reviews, and Playbook insights;
- Content Pillar performance comparisons;
- recent-vs-previous Content Pillar interest trend signals;
- platform performance comparisons;
- title-pattern analysis for packaging learnings;
- structured content reviews;
- transparent data-assisted review suggestions against the creator's own baseline;
- Creator Playbook / reusable Insights promoted from review learnings;
- dashboard summaries and high-priority topic visibility;
- email/password registration and JWT authentication;
- Docker-based local development;
- PostgreSQL migrations and GitHub Actions CI.

Initial platform catalog:

- Xiaohongshu
- Bilibili
- WeChat Official Accounts
- YouTube

## Product loop

```text
Inspiration
    ↓
Topic + Score
    ↓
Content Workspace
    ↓
Publication(s)
    ↓
Metric Snapshots
    ↓
Analytics + Review
    ↓
Creator Playbook Insight
    ↓
Better next Topic
```

A single `Content` can have multiple `Publication` records. The same core idea can therefore be adapted to several platforms with different titles, schedules, links, and performance data without losing the relationship to the original content asset.

## Analytics philosophy

Creator Ops avoids dashboards that only report vanity totals. The analytics layer is designed to answer operational questions:

- Which Content Pillars perform best?
- Is audience interest in a Content Pillar rising or falling?
- Which platform is more efficient for this creator?
- Which title patterns correlate with stronger outcomes?
- Did this content beat the creator's own baseline?
- What should change in the next iteration?

The first review assistant is deliberately rule-based and transparent. It does not require a proprietary LLM to create useful feedback, and it never overwrites the creator's review without an explicit action.

## Tech stack

| Layer | Choice |
| --- | --- |
| Web | Next.js + React + TypeScript |
| API | FastAPI + Python |
| Database | PostgreSQL |
| ORM / migrations | SQLAlchemy + Alembic |
| Authentication | Argon2 password hashing + signed JWT |
| Local runtime | Docker Compose |
| CI | GitHub Actions |

## Repository structure

```text
creator-ops/
├── apps/
│   ├── web/                 # Next.js creator workspace
│   └── api/                 # FastAPI REST API
├── docs/                    # Architecture, database, API, deployment and brand docs
├── .github/                 # CI, issue templates and PR template
├── docker-compose.yml
├── Makefile
├── .env.example
├── LICENSE
└── README.md
```

## Run locally

Requirements: Docker with Compose support.

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- Creator workspace: `http://localhost:3000`
- Login / registration: `http://localhost:3000/login`
- API: `http://localhost:8000`
- Swagger API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

The API container applies `alembic upgrade head` before starting.

Local development defaults to the seeded creator identity, so the workflow can be explored immediately. You can also create a real account on `/login`; the web client attaches the returned Bearer token automatically.

To reset all local PostgreSQL data:

```bash
docker compose down -v
```

## Run without Docker

Backend:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

## Test

Backend:

```bash
cd apps/api
pytest
```

Frontend:

```bash
cd apps/web
npm run typecheck
npm run build
```

GitHub Actions verifies Python compilation, migration upgrade/downgrade, backend tests including the complete creator workflow and feature-specific integrations, frontend type checking, and the production web build.

## Data ownership

Creator Ops is designed as an open-source system of record, not a data trap. The Settings page can export the creator's core operational data as UTF-8 CSV. Metric snapshots can also be bulk-imported from CSV, allowing a spreadsheet or platform export to act as a bridge before direct platform integrations are available.

## Production authentication

A public deployment must disable the local creator fallback and use a strong JWT secret:

```env
APP_ENV=production
ALLOW_DEV_USER_FALLBACK=false
JWT_SECRET_KEY=<strong-random-secret>
NEXT_PUBLIC_REQUIRE_AUTH=true
```

The API refuses to boot in production with the unsafe development authentication defaults.

See [`docs/deployment.md`](docs/deployment.md) for the production checklist.

## Documentation

- [Architecture](docs/architecture.md)
- [Database design](docs/database.md)
- [API overview](docs/api.md)
- [Production deployment](docs/deployment.md)
- [Brand direction](docs/branding.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Roadmap

### P0 — workflow MVP

- [x] Inspiration inbox
- [x] Topic scoring
- [x] Content pipeline
- [x] Content workspace
- [x] Publication management
- [x] Manual analytics snapshots
- [x] Structured reviews
- [x] Dashboard
- [x] Authentication foundation
- [x] End-to-end creator loop integration test

### P1 — creator analytics

- [x] Content Pillar performance comparisons
- [x] Content Pillar interest trend signals
- [x] Platform performance comparisons
- [x] 24h / 72h / 7d / 30d performance views
- [x] Publishing calendar view
- [x] Topic / content tag relationships
- [x] Title pattern analysis
- [x] CSV metric import and operational data export
- [x] Data-assisted review suggestions
- [x] Expanded API integration coverage

### P2 — creator intelligence

- [x] Creator Playbook / reusable insights foundation
- [ ] Official platform data integrations
- [ ] Optional LLM-assisted review using Creator Playbook context
- [ ] Evidence-backed AI topic scoring suggestions
- [ ] Automated insight confidence / validation over time
- [ ] Team collaboration and roles
- [ ] Browser extension and automation hooks

## Open source

Creator Ops is released under the [MIT License](LICENSE).

Commercial hosting and advanced managed features can be built on top of the open-source core without changing the goal of keeping the essential creator workflow self-hostable.
