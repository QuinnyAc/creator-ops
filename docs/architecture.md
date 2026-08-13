# Creator Ops Architecture

## Product goal

Creator Ops is an open-source creator operations workspace that manages the full content loop:

`Inspiration -> Topic -> Content -> Publication -> Metrics -> Review`

## Planned application boundaries

### `apps/web`

Next.js frontend for the creator workspace, including topic management, content pipeline, publishing calendar, analytics, and reviews.

### `apps/api`

FastAPI backend responsible for domain logic, REST APIs, authentication integration, persistence, analytics calculations, and future platform integrations.

### `docker`

Container-related infrastructure and deployment helpers.

### `docs`

Product, architecture, database, API, and contribution documentation.

## Planned core domain entities

- User
- Inspiration
- Topic
- TopicScore
- Content
- Platform
- PlatformAccount
- Publication
- MetricSnapshot
- Review
- Tag
- ContentPillar

## Architecture principles

1. Keep Topic, Content, and Publication as separate domain concepts.
2. Support one content asset being published to multiple platforms.
3. Store analytics as metric snapshots so performance can be compared over time.
4. Keep platform-specific integrations behind clear service boundaries.
5. Build the structured workflow before adding AI features.
6. Prefer a simple monorepo that one developer can maintain.

## Planned stack

- Frontend: Next.js + React + TypeScript
- Backend: FastAPI + Python
- Database: PostgreSQL
- ORM/migrations: SQLAlchemy + Alembic
- Deployment: Docker / Docker Compose
- Source control and CI: GitHub / GitHub Actions
