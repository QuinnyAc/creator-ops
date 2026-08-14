# v0.1.0 Release Checklist

This checklist defines when Creator Ops is ready to be called a public open-source v0.1.0 release.

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
- [x] CSV import/export and demo dataset

## Security and data ownership

- [x] Email/password authentication and JWT sessions
- [x] Production configuration rejects unsafe development authentication defaults
- [x] Multi-tenant integration tests cover cross-creator reads and writes
- [ ] Final Publication dependency isolation fix merged
- [x] Creator-owned CSV exports are tenant-scoped

## Engineering

- [x] FastAPI + PostgreSQL + SQLAlchemy + Alembic
- [x] Next.js + React + TypeScript
- [x] Development and production Docker Compose stacks
- [x] Migration upgrade → downgrade → upgrade verification
- [x] Backend integration tests
- [x] Frontend typecheck and production build
- [x] Production image build validation
- [x] CodeQL scanning
- [x] GitHub Codespaces contributor environment
- [ ] Reproducible npm lockfile and `npm ci` finalized
- [ ] PostgreSQL backup/restore smoke test green

## Open source packaging

- [x] MIT License
- [x] English README
- [x] CONTRIBUTING guide
- [x] SECURITY policy
- [x] Issue templates and pull request template
- [x] Architecture, database, API, deployment, security, and brand documentation
- [x] Real product screenshots captured from the application
- [ ] Product Tour linked from README
- [x] Semantic tag-driven release workflow
- [ ] `v0.1.0` tag and GitHub Release published

## Release rule

Do not tag `v0.1.0` until every unchecked release-blocking item above is completed or explicitly moved to the post-release roadmap with a documented reason.
