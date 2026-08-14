#!/usr/bin/env bash
set -euo pipefail

if [[ "${CODESPACES:-false}" != "true" ]]; then
  exit 0
fi

WEB_URL="https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
API_URL="https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"

# Start/restart the existing Creator Ops stack. Existing named volumes are kept,
# so PostgreSQL data survives normal stop/start cycles of this codespace.
docker compose up -d --build

# Codespaces resets public port visibility to private after a restart. Restore
# the two application ports to public so shared operators can use the same URLs.
if command -v gh >/dev/null 2>&1; then
  gh codespace ports visibility 3000:public 8000:public -c "${CODESPACE_NAME}" >/dev/null 2>&1 || true
fi

cat <<EOF

Creator Ops is starting in GitHub Codespaces.
Web: ${WEB_URL}
API: ${API_URL}

If GitHub shows either forwarded port as Private, open the PORTS tab and set
ports 3000 and 8000 to Public once. The start script will try to restore Public
visibility automatically on future starts.

EOF
