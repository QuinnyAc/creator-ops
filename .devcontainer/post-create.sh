#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

set_env() {
  local key="$1"
  local value="$2"
  local tmp
  tmp="$(mktemp)"

  if grep -q "^${key}=" .env; then
    awk -v k="$key" -v v="$value" 'BEGIN { FS="=" } $1 == k { $0 = k "=" v } { print }' .env > "$tmp"
    mv "$tmp" .env
  else
    cat .env > "$tmp"
    printf '%s=%s\n' "$key" "$value" >> "$tmp"
    mv "$tmp" .env
  fi
}

# When running in GitHub Codespaces, expose only the web origin to the browser.
# Next.js proxies /api/v1 internally to the FastAPI container, so operators do
# not need to access the forwarded API port directly.
if [[ "${CODESPACES:-false}" == "true" ]]; then
  WEB_URL="https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"

  set_env "CORS_ORIGINS" "$WEB_URL"
  set_env "NEXT_PUBLIC_API_URL" "$WEB_URL"
  set_env "API_INTERNAL_URL" "http://api:8000"
  set_env "ALLOW_DEV_USER_FALLBACK" "false"
  set_env "NEXT_PUBLIC_REQUIRE_AUTH" "true"

  CURRENT_SECRET="$(grep '^JWT_SECRET_KEY=' .env | head -n1 | cut -d= -f2- || true)"
  if [[ -z "$CURRENT_SECRET" || "$CURRENT_SECRET" == development-only-* || ${#CURRENT_SECRET} -lt 32 ]]; then
    NEW_SECRET="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
    set_env "JWT_SECRET_KEY" "$NEW_SECRET"
  fi

  echo "Configured Codespaces Web URL: ${WEB_URL}"
  echo "Browser API access will use the same Web URL and be proxied internally."
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
