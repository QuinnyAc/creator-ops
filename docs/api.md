# API Overview

Creator Ops exposes a REST API under `/api/v1`.

The local Swagger UI is available at `/docs` when the FastAPI service is running.

## Current MVP resources

| Area | Endpoints |
| --- | --- |
| Dashboard | `/dashboard/summary` |
| Content pillars | `/content-pillars` |
| Tags | `/tags` |
| Inspirations | `/inspirations` and `/inspirations/{id}/convert` |
| Topics | `/topics` and `/topics/{id}/score` |
| Content | `/contents` |
| Platforms | `/platforms` |
| Platform accounts | `/platform-accounts` |
| Publications | `/publications` |
| Analytics | `/analytics/summary`, `/analytics/publications/{id}/metrics` |
| Reviews | `/reviews/content/{content_id}` |

## Development identity

The MVP currently seeds one local creator user. Requests use that user unless an `X-User-ID` header is supplied. This is a development bridge, not production authentication.

Authentication and authorization must be introduced before multi-tenant public deployment.
