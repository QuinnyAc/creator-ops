# API Overview

Creator Ops exposes a REST API under `/api/v1`.

The local Swagger UI is available at `/docs` when the FastAPI service is running.

## Current MVP resources

| Area | Endpoints |
| --- | --- |
| Authentication | `/auth/register`, `/auth/login`, `/auth/me` |
| Dashboard | `/dashboard/summary` |
| Content pillars | `/content-pillars` |
| Tags | `/tags` |
| Inspirations | `/inspirations` and `/inspirations/{id}/convert` |
| Topics | `/topics`, `/topics/{id}/score`, `/topics/{id}/tags` |
| Content | `/contents`, `/contents/{id}/tags` |
| Platforms | `/platforms` |
| Platform accounts | `/platform-accounts` |
| Publications | `/publications` |
| Analytics | `/analytics/summary`, `/analytics/pillars`, publication metrics and milestones |
| Reviews | `/reviews/content/{content_id}` |

## Authentication

Registered users receive a signed Bearer JWT access token. Authenticated clients send it as:

```http
Authorization: Bearer <access-token>
```

For local development, `ALLOW_DEV_USER_FALLBACK=true` keeps the seeded creator workspace usable without first creating an account. This fallback is rejected when `APP_ENV=production`.

## Data ownership

Creator-owned resources are always filtered using the current user ID. Platform catalog rows are global, while platform accounts and all creator workflow data belong to a user.
