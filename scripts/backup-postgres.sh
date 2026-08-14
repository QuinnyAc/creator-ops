#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${CREATOR_OPS_BACKUP_DIR:-backups}"
COMPOSE_FILE="${CREATOR_OPS_COMPOSE_FILE:-docker-compose.yml}"
ENV_FILE="${CREATOR_OPS_ENV_FILE:-}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_PATH="${1:-${BACKUP_DIR}/creator-ops-${TIMESTAMP}.dump}"
PARTIAL_PATH="${OUTPUT_PATH}.partial"

compose=(docker compose -f "${COMPOSE_FILE}")
if [[ -n "${ENV_FILE}" ]]; then
  compose+=(--env-file "${ENV_FILE}")
fi

mkdir -p "$(dirname "${OUTPUT_PATH}")"
rm -f "${PARTIAL_PATH}"

cleanup_partial() {
  rm -f "${PARTIAL_PATH}"
}
trap cleanup_partial EXIT

echo "Creating Creator Ops PostgreSQL backup..."
echo "Compose file: ${COMPOSE_FILE}"
echo "Output: ${OUTPUT_PATH}"

"${compose[@]}" exec -T db sh -ceu '
  pg_dump \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --format=custom \
    --no-owner \
    --no-privileges
' > "${PARTIAL_PATH}"

if [[ ! -s "${PARTIAL_PATH}" ]]; then
  echo "Backup failed: output file is empty." >&2
  exit 1
fi

mv "${PARTIAL_PATH}" "${OUTPUT_PATH}"
trap - EXIT

BYTES="$(wc -c < "${OUTPUT_PATH}" | tr -d ' ')"
echo "Backup complete: ${OUTPUT_PATH} (${BYTES} bytes)"
