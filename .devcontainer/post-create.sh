#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

# When running in GitHub Codespaces, expose only the web origin to the browser.
# Next.js proxies /api/v1 internally to the FastAPI container, so operators do
# not need to access the forwarded API port directly.
if [[ "${CODESPACES:-false}" == "true" ]]; then
  python3 - <<'PY'
from pathlib import Path
import os
import secrets

path = Path('.env')
lines = path.read_text().splitlines()
values = {}
order = []
for line in lines:
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        values[key] = value
        order.append(key)

name = os.environ['CODESPACE_NAME']
domain = os.environ['GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN']
web_url = f"https://{name}-3000.{domain}"

updates = {
    'CORS_ORIGINS': web_url,
    'NEXT_PUBLIC_API_URL': web_url,
    'API_INTERNAL_URL': 'http://api:8000',
    'ALLOW_DEV_USER_FALLBACK': 'false',
    'NEXT_PUBLIC_REQUIRE_AUTH': 'true',
}

current_secret = values.get('JWT_SECRET_KEY', '')
if (not current_secret or current_secret.startswith('development-only-') or len(current_secret) < 32):
    updates['JWT_SECRET_KEY'] = secrets.token_hex(32)

values.update(updates)
for key in updates:
    if key not in order:
        order.append(key)

output = []
seen = set()
for line in lines:
    if '=' in line and not line.lstrip().startswith('#'):
        key = line.split('=', 1)[0]
        if key in values:
            output.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            output.append(line)
    else:
        output.append(line)
for key in order:
    if key not in seen:
        output.append(f"{key}={values[key]}")

path.write_text('\n'.join(output) + '\n')
print(f"Configured Codespaces Web URL: {web_url}")
print("Browser API access will use the same Web URL and be proxied internally.")
PY
fi

cat <<'EOF'

Creator Ops environment is ready.
The application will start automatically when this Codespace starts.

For a normal local dev environment you can still use:
  make dev

Useful local URLs:
  Web: http://localhost:3000
  API docs: http://localhost:8000/docs

EOF
