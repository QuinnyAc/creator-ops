# Security Policy

Creator Ops is in early MVP development.

Please do not open public issues for vulnerabilities that expose credentials, private creator data, authentication bypasses, or other sensitive security problems. Instead, use GitHub's private vulnerability reporting feature when it is enabled for this repository.

Never commit real platform credentials, cookies, access tokens, private API keys, or production database passwords. Local secrets belong in `.env`, which is ignored by Git.

The current MVP uses a temporary local single-user identity and is **not** designed for public multi-tenant production deployment until authentication and authorization are implemented.
