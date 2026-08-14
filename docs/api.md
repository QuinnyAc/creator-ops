# API Overview

Creator Ops exposes a REST API under `/api/v1`.

The local Swagger UI is available at `/docs` when the FastAPI service is running.

## Current resources

| Area | Main endpoints |
| --- | --- |
| Authentication / profile | `/auth/register`, `/auth/login`, `GET /auth/me`, `PATCH /auth/me` |
| Dashboard | `/dashboard/summary` |
| Content pillars | `/content-pillars` |
| Tags | `/tags` |
| Inspirations | `/inspirations`, `/inspirations/{id}/convert` |
| Topics | `/topics`, `/topics/{id}/score`, `/topics/{id}/tags` |
| Topic recommendations | `/recommendations/topics` |
| Content | `/contents`, `/contents/{id}/tags` |
| Platforms | `/platforms` |
| Platform accounts | `/platform-accounts` |
| Publications | `/publications` |
| Analytics overview | `/analytics/summary`, `/analytics/pillars`, `/analytics/platforms` |
| Tag analytics | `/analytics/tags` |
| Interest trends | `/analytics/pillar-trends?window_days=30` |
| Title analysis | `/analytics/title-patterns` |
| Publication metrics | `/analytics/publications/{publication_id}/metrics` |
| Performance milestones | `/analytics/publications/{publication_id}/milestones` |
| Reviews | `/reviews/content/{content_id}` |
| Data-assisted review | `/reviews/content/{content_id}/suggestions` |
| Creator Playbook | `/insights`, `/insights/from-content/{content_id}` |
| CSV exports | `/exports/topics.csv`, `/exports/contents.csv`, `/exports/publications.csv`, `/exports/reviews.csv`, `/exports/insights.csv` |
| Metric CSV import | `/imports/metrics.csv` |

## Authentication and creator profile

Registered users receive a signed Bearer JWT access token. Authenticated clients send it as:

```http
Authorization: Bearer <access-token>
```

`GET /auth/me` returns the current creator profile. `PATCH /auth/me` updates creator-level workspace settings currently including:

```json
{
  "display_name": "Creator name",
  "timezone": "Asia/Shanghai"
}
```

Timezone values are validated against the IANA timezone database. The saved timezone is the workspace-level source of truth used by publishing calendar date grouping, scheduled-time conversion, and publication time display.

For local development, `ALLOW_DEV_USER_FALLBACK=true` keeps the seeded creator workspace usable without first creating an account. This fallback is rejected when `APP_ENV=production`.

## Analytics semantics

Analytics aggregate the **latest MetricSnapshot for each Publication** unless an endpoint explicitly describes a time milestone or history view.

The important distinction is:

```text
Content
  └── Publication A / Xiaohongshu
  │      └── MetricSnapshot(s)
  └── Publication B / Bilibili
         └── MetricSnapshot(s)
```

This lets one reusable content asset have different titles, schedules, URLs, and performance on different platforms.

`/analytics/pillar-trends` compares published content in a recent time window against the immediately preceding window. The default is recent 30 days versus the previous 30 days. A ±20% change in average views is currently used as the transparent trend threshold.

## Evidence-backed topic recommendations

`GET /recommendations/topics` ranks already-scored candidate Topics without changing their original human score.

The recommendation layer keeps two values separate:

```text
Human Priority Score
        +
Transparent evidence adjustment
        =
Recommended Score
```

Current evidence includes Content Pillar historical average views, favorite rate, and recent-vs-previous trend signals. The response includes the exact reasons for every adjustment so the ranking is inspectable instead of acting like an opaque AI score.

## Data-assisted review

`GET /reviews/content/{content_id}/suggestions` does not call an external model. It compares the selected content's latest publication metrics against the creator's current overall baseline and combines that with title-pattern classification.

The endpoint returns:

- content metrics;
- creator baseline metrics;
- detected title patterns;
- suggested strengths;
- suggested weaknesses;
- a reusable learning draft;
- a next-action draft.

The web UI requires an explicit user action before these suggestions replace fields in the review form.

## Creator Playbook

A Review can promote its `learnings` into a reusable Insight:

```text
Review.learnings
      ↓
POST /insights/from-content/{content_id}
      ↓
Insight / Creator Playbook
```

Promotion is idempotent per Review: promoting the same Review again refreshes the existing Insight instead of creating duplicates.

## CSV metric import

`POST /imports/metrics.csv` accepts raw `text/csv`.

Required columns:

```text
publication_id,captured_at
```

Optional metric columns:

```text
views,likes,comments,favorites,shares,followers_gained,extra_metrics
```

`extra_metrics` is a JSON object encoded inside the CSV cell. The combination `(publication_id, captured_at)` acts as an upsert key, matching the database uniqueness rule for metric snapshots.

## Data ownership

Creator-owned resources are filtered using the current user ID. Platform catalog rows are global, while platform accounts and all creator workflow data belong to a user. Import, export, analytics, reviews, recommendations, and Playbook endpoints preserve the same ownership boundary.
