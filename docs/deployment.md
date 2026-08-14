# Production Deployment

Creator Ops is container-friendly and can be deployed anywhere that can run the Next.js web app, FastAPI API, and PostgreSQL.

The repository contains two Compose stacks with intentionally different goals:

- `docker-compose.yml` — local development with source mounts, Next.js dev server, and FastAPI reload;
- `docker-compose.prod.yml` — production-style images with no source mounts, no API reload, Next.js standalone output, health checks, and required secrets.

## Required production settings

Never deploy with the development authentication fallback enabled.

Copy the example first:

```bash
cp .env.production.example .env.production
```

Then replace every placeholder with real values. The important settings are:

```env
POSTGRES_PASSWORD=<strong-database-password>
JWT_SECRET_KEY=<strong-random-secret>
CORS_ORIGINS=https://your-creator-ops-domain.example
NEXT_PUBLIC_API_URL=https://api.your-creator-ops-domain.example
```

The production Compose file hard-codes these safe authentication choices:

```env
APP_ENV=production
ALLOW_DEV_USER_FALLBACK=false
NEXT_PUBLIC_REQUIRE_AUTH=true
```

Generate a strong JWT secret with a cryptographically secure random generator, for example:

```bash
openssl rand -hex 32
```

The API refuses to boot in `production` when the development fallback remains enabled or the development JWT secret is still configured.

## Validate the production stack

Before starting containers:

```bash
make prod-config
```

This expands and validates `docker-compose.prod.yml` with `.env.production`.

Build both production images:

```bash
make prod-build
```

Start the production-style stack:

```bash
make prod-up
```

Stop it without deleting PostgreSQL data:

```bash
make prod-down
```

You can point the Make targets to a different environment file:

```bash
make prod-up PROD_ENV=.env.staging
```

## Production container behavior

### Web

`apps/web/Dockerfile.prod` uses a multi-stage Next.js build and copies only the `standalone` server output plus static assets into the runtime image. The runtime process is:

```text
node server.js
```

`NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_REQUIRE_AUTH` are browser-facing Next.js variables, so they are supplied as **build arguments**. Rebuild the web image when the public API URL changes.

### API

`apps/api/Dockerfile.prod` installs only runtime Python dependencies and runs as a non-root system user.

The production Compose command performs:

```text
alembic upgrade head
→
uvicorn app.main:app --workers <API_WORKERS>
```

The API health check calls `/health` before the web service is considered ready to start.

### PostgreSQL

The production Compose stack does not publish PostgreSQL port `5432` to the host. The database is reachable by the API on the internal Compose network and stores data in the `creator_ops_postgres` named volume.

For a managed deployment, replacing the Compose PostgreSQL service with a managed PostgreSQL connection is also valid; set `DATABASE_URL` accordingly in the API runtime environment.

## CI validation

GitHub Actions validates three release-critical areas on every supported branch / pull request:

1. **Backend** — Python compilation, Alembic upgrade → downgrade → upgrade, and pytest.
2. **Frontend** — TypeScript typecheck and Next.js production build.
3. **Production containers** — production Compose config plus production API and Web Docker image builds.

A green application build therefore does not hide a broken production Dockerfile.

## Architecture

A normal hosted deployment contains three services:

1. **Web** — Next.js standalone application.
2. **API** — FastAPI application; run `alembic upgrade head` before serving traffic.
3. **PostgreSQL** — persistent database with regular backups.

In a public deployment, place the Web and API behind HTTPS. They can share one reverse proxy or be exposed on separate domains such as:

```text
https://creator.example.com
https://api.creator.example.com
```

Set `CORS_ORIGINS` to the real Web origin, not `*`.

## Minimum production checklist

- use HTTPS for both web and API;
- restrict CORS to the real frontend origin;
- use a non-default PostgreSQL password;
- keep the database inaccessible from the public internet when the provider supports private networking;
- enable automated PostgreSQL backups;
- store secrets in the deployment platform's secret manager or protected environment configuration;
- set a strong `JWT_SECRET_KEY`;
- rebuild Web when `NEXT_PUBLIC_API_URL` changes;
- run migrations before each release;
- keep platform API credentials, cookies, and tokens out of Git;
- inspect the latest GitHub Actions result before releasing;
- test restoring a database backup before relying on it.

## Current authentication scope

The MVP supports email/password registration and login with Argon2 password hashing and signed Bearer JWT access tokens. Password reset, email verification, refresh tokens, OAuth login, rate limiting, and organization/team roles remain future hardening work.

## Platform integrations

Creator Ops currently manages publication records, manually entered analytics, and CSV metric imports. Do not add brittle browser-login automation or store raw creator platform passwords. Future platform integrations should prefer official APIs and OAuth where available.
