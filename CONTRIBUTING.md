# Contributing to Creator Ops

Thanks for helping build an open creator operations system.

## Product principles

Before adding a feature, check whether it strengthens the core loop:

`Inspiration -> Topic -> Content -> Publication -> Metrics -> Review`

Creator Ops should remain a focused creator operating system rather than becoming a generic project-management tool.

## Development setup

1. Fork or clone the repository.
2. Copy `.env.example` to `.env`.
3. Run `docker compose up --build`.
4. Open the web app on port `3000` and API docs on port `8000/docs`.

## Branches

Use focused branches such as:

- `feat/topic-scoring`
- `fix/publication-date`
- `docs/analytics-model`

## Before opening a pull request

Run the relevant checks:

```bash
cd apps/api && pytest
cd apps/web && npm run typecheck && npm run build
```

If your change modifies the database, include an Alembic migration and verify both upgrade and downgrade paths.

## Pull requests

Keep pull requests small enough to review. Explain:

- the user problem being solved;
- the product behavior before and after;
- schema or API changes;
- how the change was tested;
- screenshots for visible UI changes when available.

## Commit style

Creator Ops uses conventional-style commit prefixes such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, and `chore:`.
