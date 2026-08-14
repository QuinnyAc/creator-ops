#!/usr/bin/env bash
set -euo pipefail

if [[ "${CODESPACES:-false}" != "true" ]]; then
  exit 0
fi

WEB_URL="https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"

# Refresh the Codespaces-specific .env on every start so an existing Codespace
# picks up routing/auth configuration changes without being rebuilt.
bash .devcontainer/post-create.sh >/dev/null

# Docker-in-Docker can still be starting when Codespaces runs postStartCommand.
# Wait for the daemon instead of failing the whole application startup.
echo "Waiting for Docker daemon..."
for _ in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon did not become ready in time." >&2
  exit 1
fi

# Start/restart the existing Creator Ops stack. Existing named volumes are kept,
# so PostgreSQL data survives normal stop/start cycles of this codespace.
echo "Starting Creator Ops..."
docker compose up -d --build

# Wait for local listeners. Browser traffic only needs the web port; FastAPI is
# reached by Next.js over the internal Docker network.
for port in 3000 8000; do
  for _ in $(seq 1 60); do
    if curl -fsS "http://localhost:${port}" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
done

# Restore the shared web port to public after lifecycle changes. Port 8000 does
# not need to be public because the web container proxies API requests internally.
if command -v gh >/dev/null 2>&1; then
  gh codespace ports visibility 3000:public -c "${CODESPACE_NAME}" >/dev/null 2>&1 || true
fi

cat <<EOF

Creator Ops is ready in GitHub Codespaces.
Web: ${WEB_URL}
API: proxied through ${WEB_URL}/api/v1

EOF
