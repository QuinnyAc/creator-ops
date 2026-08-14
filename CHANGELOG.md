# Changelog

All notable changes to Creator Ops will be documented in this file.

Creator Ops follows Semantic Versioning for public version tags.

## [Unreleased]

## [0.1.0] - 2026-08-14

### Added

- Inspiration Inbox with conversion into structured Topics.
- Weighted topic opportunity and priority scoring.
- Searchable Topic Library with Content Pillar, status, and Tag filters.
- Evidence-backed next-topic recommendations grounded in creator history.
- Content production Kanban and per-content workspace.
- Multi-platform creator accounts, publication records, and monthly publishing calendar.
- Time-series metric snapshots with 24h, 72h, 7d, and 30d milestones.
- Analytics by Content Pillar, platform, Tag, title pattern, and recent interest trend.
- Structured Reviews with transparent data-assisted suggestions.
- Creator Playbook / reusable Insights promoted from Review learnings.
- CSV metric import and operational data exports.
- Email/password authentication with Argon2 and signed JWT access tokens.
- Idempotent development demo workspace seed and real application screenshots.
- Screenshot-based Product Tour.
- Development and production Docker stacks.
- GitHub Codespaces Dev Container.
- PostgreSQL custom-format backup and guarded clean-schema restore operations.
- A real backup → mutation → restore CI smoke test.
- Reproducible npm dependency lockfile and `npm ci` build paths.
- Dependabot maintenance for npm, pip, and GitHub Actions.
- Tag-driven release validation and GitHub Release automation.

### Changed

- Upgraded Next.js to 16.3.1 to move the frontend onto the audited dependency chain used for the first public release.
- Frontend CI now blocks high-severity `npm audit` findings.
- Production and CI frontend builds use the committed npm lockfile.

### Security

- Production startup rejects the development authentication fallback.
- Production startup requires a non-default JWT secret.
- Production PostgreSQL is not exposed to the host by the production Compose stack.
- Creator-owned API resources are tenant-scoped and covered by adversarial integration tests.
- Publication dependency lookups return not-found for foreign creator-owned Content and Platform Accounts to avoid cross-tenant existence disclosure.
- CodeQL scans the repository and the frontend dependency audit is release-blocking at high severity.

## Release process

Public releases use tags in the form `vMAJOR.MINOR.PATCH`, for example `v0.1.0`.
The release workflow validates backend migrations/tests, demo seeding, the frontend dependency install, typecheck/build, and production container builds before creating a GitHub Release from the tag.
