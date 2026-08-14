#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

cat <<'EOF'

Creator Ops development environment is ready.

Start the application:
  make dev

After the containers are healthy, seed the realistic demo dataset in another terminal:
  make demo

Useful URLs after port forwarding:
  Web: http://localhost:3000
  API docs: http://localhost:8000/docs

EOF
