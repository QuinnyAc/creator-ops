#!/usr/bin/env bash
set -euo pipefail

if [[ "${CODESPACES:-false}" != "true" ]]; then
  exit 0
fi

WEB_URL="https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
API_URL="https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"

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

# Wait briefly for the web and API listeners so a newly attached user does not
# open the forwarded URL before the services are actually accepting traffic.
for port in 3000 8000; do
  for _ in $(seq 1 60); do
    if curl -fsS "http://localhost:${port}" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
done

# Codespaces can restore forwarded ports as private after lifecycle changes.
# Try to restore both application ports to public for the shared workspace.
if command -v gh >/dev/null 2>&1; then
  gh codespace ports visibility 3000:public 8000:public -c "${CODESPACE_NAME}" >/dev/null 2>&1 || true
fi

cat <<EOF

Creator Ops is ready in GitHub Codespaces.
Web: ${WEB_URL}
API: ${API_URL}

EOF
