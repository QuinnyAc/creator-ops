# Creator Ops

Open-source creator operations management system.

Creator Ops is a one-stop workspace for individual creators and small content teams to manage the full content production loop:

`Inspiration -> Topic -> Content -> Publication -> Metrics -> Review`

## Project status

Early MVP development. The repository now contains the initial product architecture, PostgreSQL domain schema, FastAPI application bootstrap, Alembic migration, and Docker Compose development environment.

## Stack

- Next.js + React + TypeScript
- FastAPI + Python
- PostgreSQL
- SQLAlchemy + Alembic
- Docker / Docker Compose
- GitHub Actions

## Repository structure

```text
creator-ops/
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # FastAPI backend
├── docker/           # Container/deployment helpers
├── docs/             # Product and engineering documentation
├── docker-compose.yml
├── .env.example
├── .editorconfig
├── .gitignore
└── README.md
```

## Local development

Copy the example environment file:

```bash
cp .env.example .env
```

Start PostgreSQL and the API:

```bash
docker compose up --build
```

The API will be available at:

- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`

Docker Compose runs `alembic upgrade head` before starting the FastAPI development server.

To run the API without Docker:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Run backend tests:

```bash
cd apps/api
pytest
```

## Domain model

The core domain chain is:

```text
Inspiration
  -> Topic
  -> Content
  -> Publication
  -> MetricSnapshot
  -> Review
```

A content asset and a platform publication are deliberately different entities so one piece of content can be adapted to multiple accounts and platforms.

See:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/database.md`](docs/database.md)

## MVP roadmap

1. Topic management and scoring
2. Content production pipeline
3. Publication management
4. Manual analytics recording
5. Structured content reviews
6. Creator dashboard

## License

License selection is pending.
