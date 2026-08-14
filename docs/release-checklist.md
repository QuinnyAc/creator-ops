# v0.1.0 Release Checklist

This checklist defines the public open-source v0.1.0 release standard for Creator Ops.

## Product

- [x] Inspiration capture and conversion to Topics
- [x] Topic scoring, taxonomy, filtering, and recommendations
- [x] Creator-native Content Pipeline and Content Workspace
- [x] Platform accounts and platform-specific Publications
- [x] Publishing calendar
- [x] Metric snapshots and milestone views
- [x] Analytics by Content Pillar, platform, Tag, title pattern, and recent trend
- [x] Structured Reviews and data-assisted review suggestions
- [x] Creator Playbook Insights
- [x] CSV import/export and reproducible demo dataset

## Security and data ownership

- [x] Email/password authentication and JWT sessions
- [x] Production configuration rejects unsafe development authentication defaults
- [x] Multi-tenant integration tests cover cross-creator reads and writes
- [x] Publication dependency lookups do not disclose foreign creator-owned objects
- [x] Creator-owned CSV exports are tenant-scoped
- [x] CodeQL security scanning
- [x] Frontend CI blocks high-severity npm audit findings

## Engineering

- [x] FastAPI + PostgreSQL + SQLAlchemy + Alembic
- [x] Next.js + React + TypeScript
- [x] Development and production Docker Compose stacks
- [x] Migration upgrade → downgrade → upgrade verification
- [x] Backend integration tests
- [x] Frontend typecheck and production build
- [x] Production image build validation
- [x] GitHub Codespaces contributor/demo environment
- [x] Reproducible npm lockfile and `npm ci`
- [x] Dependabot for npm, pip, and GitHub Actions
- [x] PostgreSQL backup/restore scripts and a real restore smoke test

## Open source packaging

- [x] MIT License
- [x] English README
- [x] CONTRIBUTING guide
- [x] SECURITY policy
- [x] Issue templates and pull request template
- [x] Architecture, database, API, deployment, backup, security, and brand documentation
- [x] Real product screenshots captured from the application
- [x] Screenshot-based Product Tour
- [x] Semantic tag-driven release workflow
- [ ] `v0.1.0` tag and GitHub Release published

## Release rule

The release tag must point to the final `main` commit after every release-blocking item above is complete. The tag-driven Release workflow must then validate backend migrations/tests, demo seeding, frontend typecheck/build, and production containers before the GitHub Release is considered complete.
