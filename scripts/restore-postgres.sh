#!/usr/bin/env bash
set -euo pipefail

BACKUP_PATH="${1:-}"
COMPOSE_FILE="${CREATOR_OPS_COMPOSE_FILE:-docker-compose.yml}"
ENV_FILE="${CREATOR_OPS_ENV_FILE:-}"

if [[ -z "${BACKUP_PATH}" ]]; then
  echo "Usage: CREATOR_OPS_RESTORE_CONFIRM=YES $0 <backup.dump>" >&2
  exit 2
fi

if [[ ! -f "${BACKUP_PATH}" ]]; then
  echo "Backup file does not exist: ${BACKUP_PATH}" >&2
  exit 2
fi

if [[ ! -s "${BACKUP_PATH}" ]]; then
  echo "Backup file is empty: ${BACKUP_PATH}" >&2
  exit 2
fi

if [[ "${CREATOR_OPS_RESTORE_CONFIRM:-}" != "YES" ]]; then
  cat >&2 <<'EOF'
Restore refused.

This operation replaces Creator Ops PostgreSQL data.
Re-run with CREATOR_OPS_RESTORE_CONFIRM=YES after verifying the backup path.
EOF
  exit 3
fi

compose=(docker compose -f "${COMPOSE_FILE}")
if [[ -n "${ENV_FILE}" ]]; then
  compose+=(--env-file "${ENV_FILE}")
fi

resume_services() {
  echo "Starting Creator Ops API and Web services..."
  "${compose[@]}" start api web >/dev/null 2>&1 || true
}
trap resume_services EXIT

echo "Stopping Creator Ops API and Web before restore..."
"${compose[@]}" stop api web

echo "Restoring PostgreSQL from: ${BACKUP_PATH}"
"${compose[@]}" exec -T db sh -ceu '
  pg_restore \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    --exit-on-error
' < "${BACKUP_PATH}"

echo "Restore complete. API startup will re-run Alembic migrations if required."
