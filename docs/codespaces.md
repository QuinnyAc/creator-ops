# GitHub Codespaces

Creator Ops includes a Dev Container definition so contributors can work from GitHub Codespaces without installing the application toolchain on their host machine.

## Start a Codespace

From the Creator Ops repository on GitHub:

1. choose **Code**;
2. open the **Codespaces** tab;
3. create a Codespace from the branch you want to work on.

The Dev Container provides an Ubuntu development environment with Docker-in-Docker and forwards the Creator Ops Web/API ports.

The post-create script copies `.env.example` to `.env` when an environment file does not already exist. It does **not** start application containers automatically, so contributors remain in control of build time and resource usage.

## Start Creator Ops

In the Codespaces terminal:

```bash
make dev
```

This runs the normal repository `docker-compose.yml`; Codespaces does not use a separate product runtime.

After the stack is healthy, open another terminal and seed the realistic demo workspace:

```bash
make demo
```

Forwarded services:

- Web — port `3000`
- FastAPI / Swagger — port `8000`

Codespaces normally opens or offers the forwarded Web port automatically according to your GitHub settings.

## Stop or reset

```bash
make down
```

To remove the local PostgreSQL volume and start from a clean database:

```bash
make reset
```

The next `make dev` run applies Alembic migrations again.

## Why the Dev Container uses Docker-in-Docker

Creator Ops already defines its development environment in Docker Compose. Reusing that same stack inside Codespaces keeps these paths aligned:

```text
local Docker development
        =
Codespaces development
        =
CI application topology
```

This avoids a second set of Python/Node/PostgreSQL installation instructions that can drift from the real application containers.

## Secrets

Do not commit real platform credentials, JWT secrets, database passwords, or third-party API keys to `.env`.

For future platform integrations, use GitHub Codespaces secrets or another protected secret mechanism. Keep `.env.example` limited to safe development defaults and variable names.

## Resource usage

Codespaces is a developer environment, not the public hosted demo. Stop or delete Codespaces you no longer need according to your GitHub account's resource policy.
