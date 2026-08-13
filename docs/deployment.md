# Production Deployment

Creator Ops is container-friendly and can be deployed anywhere that can run the Next.js web app, FastAPI API, and PostgreSQL.

## Required production settings

Never deploy with the development authentication fallback enabled.

```env
APP_ENV=production
ALLOW_DEV_USER_FALLBACK=false
JWT_SECRET_KEY=<strong-random-secret>
CORS_ORIGINS=https://your-creator-ops-domain.example
NEXT_PUBLIC_API_URL=https://api.your-creator-ops-domain.example
NEXT_PUBLIC_REQUIRE_AUTH=true
```

Generate a strong JWT secret with a cryptographically secure random generator, for example `openssl rand -hex 32`.

The API refuses to boot in `production` when either the development fallback remains enabled or the default development JWT secret is still configured.

## Architecture

A normal hosted deployment contains three services:

1. **Web** — Next.js application.
2. **API** — FastAPI application; run `alembic upgrade head` before serving traffic.
3. **PostgreSQL** — persistent database with regular backups.

## Minimum production checklist

- use HTTPS for both web and API;
- restrict CORS to the real frontend origin;
- use a non-default PostgreSQL password;
- keep the database inaccessible from the public internet when the provider supports private networking;
- enable database backups;
- set `APP_ENV=production`;
- set `ALLOW_DEV_USER_FALLBACK=false`;
- set a strong `JWT_SECRET_KEY`;
- set `NEXT_PUBLIC_REQUIRE_AUTH=true`;
- run migrations before each release;
- keep platform API credentials, cookies, and tokens out of Git;
- review GitHub Actions before merging releases.

## Current authentication scope

The current MVP supports email/password registration and login with Argon2 password hashing and signed Bearer JWT access tokens. Password reset, email verification, refresh tokens, OAuth login, rate limiting, and organization/team roles remain future hardening work.

## Platform integrations

Creator Ops currently manages publication records and manually entered analytics. Do not add brittle browser-login automation or store raw creator platform passwords. Future platform integrations should prefer official APIs and OAuth where available.
