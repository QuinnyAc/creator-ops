# Changelog

All notable changes to Creator Ops will be documented in this file.

This project follows Semantic Versioning once public version tags are published.

## [Unreleased]

### Added

- Inspiration Inbox with conversion into structured Topics.
- Weighted topic opportunity and priority scoring.
- Searchable Topic Library with Content Pillar, status, and Tag filters.
- Evidence-backed topic recommendations using creator history and recent Content Pillar trends.
- Content production Kanban and per-content workspace.
- Multi-platform publication records and monthly publishing calendar.
- Time-series metric snapshots with 24h, 72h, 7d, and 30d milestones.
- Analytics by Content Pillar, platform, tag, and title pattern.
- Recent-vs-previous Content Pillar trend signals.
- Structured reviews with transparent data-assisted suggestions.
- Creator Playbook / reusable Insights promoted from review learnings.
- CSV metric import and operational data exports.
- Email/password authentication with Argon2 and signed JWT access tokens.
- Production Docker images and Compose configuration.
- PostgreSQL migrations and GitHub Actions CI.

### Security

- Production startup rejects the development authentication fallback.
- Production startup requires a non-default JWT secret.

## Release process

Public releases use tags in the form `vMAJOR.MINOR.PATCH`, for example `v0.1.0`.
The release workflow validates backend migrations/tests and the frontend production build before creating a GitHub Release from the tag.
