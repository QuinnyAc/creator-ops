.PHONY: dev down reset test test-api typecheck build-web

dev:
	docker compose up --build

down:
	docker compose down

reset:
	docker compose down -v

test: test-api typecheck

test-api:
	cd apps/api && pytest

typecheck:
	cd apps/web && npm run typecheck

build-web:
	cd apps/web && npm run build
