# Creator Ops

> An open-source creator operations workspace — from idea to insight.

Creator Ops helps individual creators and small content teams manage the full content production loop in one place:

**Inspiration → Topic → Content → Publication → Metrics → Review → Better next topic**

It is intentionally not another generic Notion-style database. The product understands the domain relationship between a topic, a reusable content asset, each platform-specific publication, its time-series metrics, and the learning produced by a review.

## Current MVP

The repository now includes a working first-pass product architecture for:

- low-friction inspiration inbox;
- structured topic database and weighted topic scoring;
- tags attached to topics and content assets;
- content production Kanban and per-content workspace;
- multi-platform account and publication management;
- monthly publishing calendar;
- manual metric snapshots and 24h / 72h / 7d / 30d milestones;
- Content Pillar performance analytics;
- structured content reviews;
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
Learning → Next Topic
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
- [x] 24h / 72h / 7d / 30d performance views
- [x] Publishing calendar view
- [x] Topic / content tag relationships
- [ ] Title pattern analysis
- [ ] CSV import / export
- [ ] More API integration coverage

### P2 — creator intelligence

- [ ] Platform data integrations
- [ ] AI-assisted review
- [ ] AI topic scoring suggestions
- [ ] Creator Playbook / reusable insights
- [ ] Team collaboration and roles
- [ ] Browser extension and automation hooks

## Open source

Creator Ops is released under the [MIT License](LICENSE).

Commercial hosting and advanced managed features can be built on top of the open-source core without changing the goal of keeping the essential creator workflow self-hostable.
