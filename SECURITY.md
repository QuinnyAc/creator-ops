# Security Policy

Creator Ops is in active MVP development.

Please do not open public issues for vulnerabilities that expose credentials, private creator data, authentication bypasses, or other sensitive security problems. Instead, use GitHub's private vulnerability reporting feature when it is enabled for this repository.

Never commit real platform credentials, cookies, access tokens, private API keys, JWT secrets, or production database passwords. Local secrets belong in `.env`, which is ignored by Git.

## Authentication

Creator Ops supports email/password registration and login. Passwords are stored as modern password hashes and the API issues signed Bearer JWT access tokens.

The local development environment can deliberately fall back to a seeded creator identity. That mode exists only to keep self-hosted MVP development friction low. The API rejects production startup when the fallback is enabled or the default development JWT secret is used.

Public deployments should additionally add provider-level rate limiting, HTTPS, database backups, password reset/email verification, and operational monitoring before handling sensitive creator data at scale.
