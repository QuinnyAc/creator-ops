# Changelog

All notable changes to Creator Ops will be documented in this file.

Creator Ops follows Semantic Versioning once public version tags are published.

## [Unreleased]

### Added

- Inspiration Inbox with conversion into structured Topics.
- Weighted topic opportunity and priority scoring.
- Searchable Topic Library with Content Pillar, status, and Tag filters.
- Evidence-backed next-topic recommendations grounded in creator history.
- Content production Kanban and per-content workspace.
- Multi-platform publication records and monthly publishing calendar.
- Time-series metric snapshots with 24h, 72h, 7d, and 30d milestones.
- Analytics by Content Pillar, platform, Tag, title pattern, and recent interest trend.
- Structured Reviews with transparent data-assisted suggestions.
- Creator Playbook / reusable Insights promoted from Review learnings.
- CSV metric import and operational data exports.
- Email/password authentication with Argon2 and signed JWT access tokens.
- Idempotent development demo workspace seed.
- Development and production Docker stacks.
- PostgreSQL migrations and GitHub Actions CI.

### Security

- Production startup rejects the development authentication fallback.
- Production startup requires a non-default JWT secret.
- Production PostgreSQL is not exposed to the host by the production Compose stack.

## Release process

Public releases use tags in the form `vMAJOR.MINOR.PATCH`, for example `v0.1.0`.
The release workflow validates backend migrations/tests, demo seeding, the frontend production build, and production container builds before creating a GitHub Release from the tag.
