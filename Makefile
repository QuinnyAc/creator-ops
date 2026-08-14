.PHONY: dev down reset demo test test-api typecheck build-web prod-config prod-build prod-up prod-down

PROD_ENV ?= .env.production

dev:
	docker compose up --build

down:
	docker compose down

reset:
	docker compose down -v

demo:
	docker compose exec api python -m app.demo_seed

test: test-api typecheck

test-api:
	cd apps/api && pytest

typecheck:
	cd apps/web && npm run typecheck

build-web:
	cd apps/web && npm run build

prod-config:
	docker compose --env-file $(PROD_ENV) -f docker-compose.prod.yml config

prod-build:
	docker compose --env-file $(PROD_ENV) -f docker-compose.prod.yml build

prod-up:
	docker compose --env-file $(PROD_ENV) -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose --env-file $(PROD_ENV) -f docker-compose.prod.yml down
