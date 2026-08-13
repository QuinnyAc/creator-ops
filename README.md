# Creator Ops

Open-source creator operations management system.

Creator Ops is being built as a one-stop workspace for individual creators and small content teams to manage the full content production loop:

`Inspiration -> Topic -> Content -> Publication -> Metrics -> Review`

## Project status

Early development. The project is currently establishing its product architecture and technical foundation.

## Planned stack

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
├── .env.example
├── .editorconfig
├── .gitignore
└── README.md
```

See [`docs/architecture.md`](docs/architecture.md) for the initial architecture decisions.

## Roadmap

The first MVP will focus on:

1. Topic management and scoring
2. Content production pipeline
3. Publication management
4. Manual analytics recording
5. Structured content reviews

## License

License selection is pending.
