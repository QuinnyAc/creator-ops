# Security Model

Creator Ops is designed around creator-owned data boundaries. The current MVP is not a team/organization product yet, so the primary authorization boundary is the authenticated `User`.

## Ownership model

Global catalog data:

- `Platform`

Creator-owned data:

- Inspirations
- Content Pillars
- Tags
- Topics and Topic Scores
- Content
- Platform Accounts
- Publications (ownership inherited through Content)
- Metric Snapshots (ownership inherited through Publication → Content)
- Reviews (ownership inherited through Content)
- Creator Playbook Insights

Every creator-owned list query is scoped to the current user. Direct-object routes resolve ownership before returning or mutating the object.

## Cross-tenant behavior

When an authenticated user requests another creator's object by ID, Creator Ops returns `404 Not Found` rather than exposing whether the foreign object exists.

Examples covered by integration tests include:

- reading, updating, or deleting another creator's Content;
- creating a Publication using another creator's Content;
- creating a Publication using another creator's Platform Account;
- reading or writing MetricSnapshots for another creator's Publication;
- reading or updating another creator's Review;
- promoting or modifying another creator's Creator Playbook Insight;
- exporting another creator's Topics, Content, Publications, Reviews, or Insights.

The test suite creates two real authenticated users and actively attempts these cross-tenant operations. This is intentionally stronger than testing helper functions in isolation.

## Authentication modes

### Development

Local development can use the seeded creator identity when:

```env
ALLOW_DEV_USER_FALLBACK=true
```

This exists so contributors can explore the product loop immediately after starting Docker.

### Production

Production must use real authentication:

```env
APP_ENV=production
ALLOW_DEV_USER_FALLBACK=false
JWT_SECRET_KEY=<strong-random-secret>
```

The API rejects unsafe production authentication defaults during startup.

Passwords are hashed with Argon2. API sessions use signed Bearer JWT access tokens.

## Data export boundary

CSV export is treated as a security boundary, not only a convenience feature. Every export query is scoped to the current creator before CSV serialization. Tenant-isolation tests place a unique marker in one user's data and verify that the second user's exports never contain it.

## Database constraints are not authorization

Foreign keys and cascading deletes protect relational integrity, but they do not replace application authorization. API routes must continue to verify creator ownership even when an object ID is structurally valid.

## Future team collaboration

When organization/team features are introduced, authorization should move from a single `user_id` boundary to an explicit workspace membership model with roles and permissions. Do not overload the current development fallback or infer team access from email domains.

## Reporting vulnerabilities

Please follow the process in [`SECURITY.md`](../SECURITY.md) for responsible disclosure. Do not publish exploit details in a public GitHub issue before maintainers have had an opportunity to investigate.
