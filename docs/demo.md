# Demo Data

Creator Ops includes an explicit demo-data seed for local development, product walkthroughs, screenshots, and non-production demo deployments.

The seed is **not** executed automatically. It is also blocked when `APP_ENV=production`.

## Seed the demo workspace

Start the database and apply migrations first. With Docker Compose running:

```bash
docker compose exec api python -m app.demo_seed
```

Without Docker:

```bash
cd apps/api
alembic upgrade head
python -m app.demo_seed
```

The command is idempotent. Running it again reuses the same demo entities instead of duplicating the core demo workspace.

## What it creates

The demo workspace is attached to the seeded local creator and includes:

- two Content Pillars;
- reusable Tags;
- an Inspiration Inbox item;
- scored Topics in different lifecycle states;
- published and in-production Content assets;
- Xiaohongshu and Bilibili demo accounts;
- published and scheduled Publications;
- multiple MetricSnapshots so milestone and trend views have data;
- a structured Review;
- a promoted Creator Playbook Insight.

The sample metrics are synthetic and exist only to demonstrate product behavior. They must not be presented as real creator performance data.

## Production safety

`python -m app.demo_seed` raises an error when:

```env
APP_ENV=production
```

A public production workspace should start empty or use an explicit onboarding/import flow. Never use demo metrics as customer data.

## Reset local data

To remove all local PostgreSQL data, including the seeded local creator and demo workspace:

```bash
docker compose down -v
```

Then start the stack again and rerun migrations/seed as needed.
