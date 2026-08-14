# Creator Ops

> An open-source creator operations workspace — from idea to insight.

Creator Ops helps individual creators and small content teams manage the full content production loop in one place:

**Inspiration → Topic → Content → Publication → Metrics → Review → Insight → Better next topic**

It is intentionally not another generic Notion-style database. The product understands the domain relationship between a topic, a reusable content asset, each platform-specific publication, its time-series metrics, the learning produced by a review, and the reusable insight that should influence the next creation cycle.

## Current MVP

The repository now includes a working first-pass creator operations product for:

- low-friction inspiration inbox;
- structured Topic Library with weighted topic scoring;
- keyword, Content Pillar, status, and Tag filtering for growing topic databases;
- tags attached to topics and content assets;
- content production Kanban and per-content workspace;
- multi-platform account and publication management;
- monthly publishing calendar;
- manual metric snapshots and 24h / 72h / 7d / 30d milestones;
- Content Pillar and platform performance analytics;
- title-pattern analysis for packaging learnings;
- data-assisted structured content reviews;
- Creator Insights / Playbook promoted from review learnings;
- CSV import and export workflows;
- dashboard summaries;
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
Review
    ↓
Insight / Creator Playbook
    ↓
Better next topic
```

A single `Content` can have multiple `Publication` records. That is important because the same core idea may be adapted to several platforms with different titles, schedules, links, and performance data.

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

Local development defaults to the seeded creator identity, so you can use the workflow immediately. You can also create a real account on `/login` and the web client will attach the returned Bearer token automatically.

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

GitHub Actions verifies Python compilation, migration upgrade/downgrade, backend tests including the complete creator workflow, frontend type checking, and the production web build.

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
- [x] Searchable/filterable Topic Library
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
- [x] Platform performance comparisons
- [x] 24h / 72h / 7d / 30d performance views
- [x] Publishing calendar view
- [x] Topic / content tag relationships
- [x] Title pattern analysis
- [x] CSV import / export
- [x] Additional feature and integration coverage
- [ ] Tag-level performance analytics
- [ ] Richer trend and cohort analysis

### P2 — creator intelligence

- [x] Data-assisted review suggestions with transparent rules
- [x] Creator Playbook / reusable insights
- [ ] AI topic scoring suggestions
- [ ] Optional LLM-assisted review and insight synthesis
- [ ] Platform data integrations
- [ ] Team collaboration and roles
- [ ] Browser extension and automation hooks

## Release readiness

The current codebase is an MVP foundation rather than a finished hosted SaaS. Before the first public release, the remaining work is mainly packaging and operations:

- keep aggregate CI green;
- configure a public demo deployment;
- add real product screenshots and a social preview image;
- finalize logo assets and brand usage;
- publish a first tagged GitHub release;
- document upgrade notes once the database schema starts evolving across public versions.

## Open source

Creator Ops is released under the [MIT License](LICENSE).

Commercial hosting and advanced managed features can be built on top of the open-source core without changing the goal of keeping the essential creator workflow self-hostable.
