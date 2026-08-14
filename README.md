# Creator Ops

> An open-source creator operations workspace — from idea to insight.

Creator Ops helps individual creators and small content teams manage the full content production loop in one place:

**Inspiration → Topic → Content → Publication → Metrics → Review → Insight → Better next topic**

It is intentionally not another generic Notion-style database. Creator Ops understands the domain relationship between a topic, a reusable content asset, each platform-specific publication, its time-series metrics, the review produced from those results, and the reusable creator knowledge that should influence the next decision.

## Why Creator Ops

Generic databases are excellent at storing rows. Creator Ops is opinionated about the creator workflow:

- capture an idea with almost no friction;
- decide whether a topic is worth making before production starts;
- manage a content lifecycle instead of a generic task lifecycle;
- separate reusable `Content` from each platform-specific `Publication`;
- preserve metric snapshots instead of overwriting yesterday's numbers;
- compare Content Pillars, Tags, platforms, title patterns, and recent interest changes;
- rank the next topics using both human judgment and the creator's own performance evidence;
- turn a one-off review into a reusable Creator Playbook insight.

## 60-second demo

Requirements: Docker with Compose support.

```bash
cp .env.example .env
docker compose up --build -d
make demo
```

Open `http://localhost:3000`.

The demo seed is development-only and intentionally populates a realistic creator workspace with:

- Inspiration Inbox items;
- scored Topics and Tags;
- multiple Content Pillars;
- content in published, review, script, and ready stages;
- Xiaohongshu, Bilibili, WeChat Official Accounts, and YouTube accounts;
- cross-platform Publications and a scheduled item;
- time-series MetricSnapshots;
- data that produces meaningful platform, tag, title, and trend analytics;
- Reviews and a Creator Playbook Insight.

Running `make demo` again is safe: the seed is idempotent. The CI pipeline executes it twice on PostgreSQL to verify that property.

To delete all local data and start again:

```bash
make reset
```

## Current MVP

The repository includes a working end-to-end product foundation for:

- low-friction Inspiration Inbox with conversion into Topics;
- searchable Topic Library with weighted opportunity / priority scoring;
- Content Pillars and Tags for stable strategy + flexible taxonomy;
- evidence-backed next-topic recommendations with transparent score adjustments;
- content production Kanban and per-content workspace;
- multi-platform creator accounts and Publication management;
- monthly publishing calendar;
- manual metric snapshots and 24h / 72h / 7d / 30d milestones;
- bulk CSV metric import with idempotent snapshot upserts;
- CSV exports for Topics, Content, Publications, Reviews, and Playbook Insights;
- Content Pillar performance comparisons;
- recent-vs-previous Content Pillar interest trend signals;
- platform performance comparisons;
- Tag performance analytics;
- title-pattern analysis for packaging learnings;
- structured content Reviews;
- transparent data-assisted review suggestions against the creator's own baseline;
- Creator Playbook / reusable Insights promoted from Review learnings;
- dashboard summaries and evidence-backed topic recommendations;
- email/password registration and JWT authentication;
- development and production Docker stacks;
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
Evidence-backed recommendation
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
- Which Tags correlate with stronger outcomes?
- Which platform is more efficient for this creator?
- Which title patterns correlate with stronger outcomes?
- Did this Content beat the creator's own baseline?
- Which scored Topic has the strongest combination of intent and historical evidence?
- What should change in the next iteration?

The first review assistant and topic recommendation engine are deliberately rule-based and transparent. They do not require a proprietary LLM to create useful feedback, and they never overwrite the creator's judgment without an explicit action.

## Tech stack

| Layer | Choice |
| --- | --- |
| Web | Next.js + React + TypeScript |
| API | FastAPI + Python |
| Database | PostgreSQL |
| ORM / migrations | SQLAlchemy + Alembic |
| Authentication | Argon2 password hashing + signed JWT |
| Local runtime | Docker Compose |
| Production packaging | Multi-stage Docker images + production Compose |
| CI | GitHub Actions |

## Repository structure

```text
creator-ops/
├── apps/
│   ├── web/                 # Next.js creator workspace
│   └── api/                 # FastAPI REST API
├── docs/                    # Architecture, database, API, deployment and brand docs
├── .github/                 # CI, issue templates and PR template
├── docker-compose.yml       # development stack
├── docker-compose.prod.yml  # production-style stack
├── Makefile
├── .env.example
├── .env.production.example
├── LICENSE
└── README.md
```

## Run locally

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

Local development defaults to the seeded creator identity, so the workflow can be explored without authentication setup. You can also create a real account on `/login`; the web client attaches the returned Bearer token automatically.

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

GitHub Actions validates three release-critical lanes:

1. **Backend** — Python compilation, Alembic upgrade → downgrade → upgrade, pytest, and the development demo seed executed twice.
2. **Frontend** — TypeScript typecheck and Next.js production build.
3. **Production containers** — production Compose validation plus production API and Web Docker image builds.

## Production-style deployment

Create a production environment file:

```bash
cp .env.production.example .env.production
```

Replace every placeholder secret and public URL, then validate and build:

```bash
make prod-config
make prod-build
make prod-up
```

The production stack:

- disables the development user fallback;
- requires a strong PostgreSQL password and JWT secret;
- runs the API without reload and as a non-root user;
- uses multiple Uvicorn workers by default;
- builds Next.js standalone output;
- does not expose PostgreSQL to the host;
- includes service health checks;
- runs Alembic migrations before the API starts.

See [`docs/deployment.md`](docs/deployment.md) for the production checklist and reverse-proxy guidance.

## Data ownership

Creator Ops is designed as an open-source system of record, not a data trap. The Settings page can export the creator's core operational data as UTF-8 CSV. Metric snapshots can also be bulk-imported from CSV, allowing a spreadsheet or platform export to act as a bridge before direct platform integrations are available.

## Production authentication

A public deployment must use safe production settings:

```env
APP_ENV=production
ALLOW_DEV_USER_FALLBACK=false
JWT_SECRET_KEY=<strong-random-secret>
NEXT_PUBLIC_REQUIRE_AUTH=true
```

The API refuses to boot in production with unsafe development authentication defaults.

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

- [x] Inspiration Inbox
- [x] Topic scoring
- [x] Content Pipeline
- [x] Content Workspace
- [x] Publication management
- [x] Manual analytics snapshots
- [x] Structured Reviews
- [x] Dashboard
- [x] Authentication foundation
- [x] End-to-end Creator Loop integration test

### P1 — creator analytics and decision support

- [x] Content Pillar performance comparisons
- [x] Content Pillar interest trend signals
- [x] Platform performance comparisons
- [x] Tag performance analytics
- [x] 24h / 72h / 7d / 30d performance views
- [x] Publishing calendar view
- [x] Topic / Content Tag relationships
- [x] Title pattern analysis
- [x] CSV metric import and operational data export
- [x] Data-assisted Review suggestions
- [x] Evidence-backed next-Topic recommendations
- [x] Expanded API integration coverage
- [x] Development demo dataset
- [x] Production container validation in CI

### P2 — creator intelligence

- [x] Creator Playbook / reusable Insights foundation
- [ ] Official platform data integrations
- [ ] Optional LLM-assisted Review using Creator Playbook context
- [ ] AI-assisted Topic evaluation grounded in creator evidence
- [ ] Automated Insight confidence / validation over time
- [ ] Team collaboration and roles
- [ ] Browser extension and automation hooks

## Open source

Creator Ops is released under the [MIT License](LICENSE).

Commercial hosting and advanced managed features can be built on top of the open-source core without changing the goal of keeping the essential creator workflow self-hostable.
