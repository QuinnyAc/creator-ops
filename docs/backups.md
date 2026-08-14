# PostgreSQL Backup and Restore

Creator Ops stores creator workflow data in PostgreSQL. A self-hosted deployment is not production-ready unless that database is backed up and the restore path has been tested.

## Backup the development stack

With the normal Docker Compose stack running:

```bash
make backup
```

The default output is a timestamped PostgreSQL custom-format dump under:

```text
backups/creator-ops-YYYYMMDDTHHMMSSZ.dump
```

You can choose an explicit output path:

```bash
./scripts/backup-postgres.sh /secure/path/creator-ops.dump
```

The script runs `pg_dump` **inside the database container** and reads `POSTGRES_USER` / `POSTGRES_DB` from that container, so it does not need to duplicate database credentials on the command line.

## Backup the production Compose stack

Point the script at the production Compose and environment files:

```bash
CREATOR_OPS_COMPOSE_FILE=docker-compose.prod.yml \
CREATOR_OPS_ENV_FILE=.env.production \
CREATOR_OPS_BACKUP_DIR=/srv/creator-ops/backups \
./scripts/backup-postgres.sh
```

A production scheduler can run the same command from cron/systemd or an infrastructure scheduler. Store backup files outside the application checkout and preferably copy them to a separate failure domain.

## Restore

Restoring is deliberately guarded because it replaces current PostgreSQL objects.

Development convenience target:

```bash
make restore BACKUP=backups/creator-ops-20260814T120000Z.dump
```

Direct script usage requires an explicit confirmation variable:

```bash
CREATOR_OPS_RESTORE_CONFIRM=YES \
./scripts/restore-postgres.sh backups/creator-ops-20260814T120000Z.dump
```

For production Compose:

```bash
CREATOR_OPS_COMPOSE_FILE=docker-compose.prod.yml \
CREATOR_OPS_ENV_FILE=.env.production \
CREATOR_OPS_RESTORE_CONFIRM=YES \
./scripts/restore-postgres.sh /srv/creator-ops/backups/creator-ops.dump
```

The restore script:

1. verifies the dump file exists and is non-empty;
2. refuses to continue without `CREATOR_OPS_RESTORE_CONFIRM=YES`;
3. stops `api` and `web` to avoid application writes during restore;
4. runs `pg_restore --clean --if-exists` inside the database container;
5. restarts API and Web on exit;
6. relies on normal API startup to apply any migrations newer than the restored database.

## Recommended production policy

At minimum:

- create automated daily backups;
- keep multiple historical copies instead of overwriting one file;
- store at least one copy outside the host running Creator Ops;
- encrypt backup storage when it contains real creator/customer data;
- restrict filesystem/object-storage access to operators who need it;
- monitor backup job failures;
- test a restore on a disposable environment on a recurring schedule.

A backup that has never been restored is only an assumption.

## Managed PostgreSQL

If Creator Ops uses a managed PostgreSQL provider, prefer the provider's native point-in-time recovery / automated backup capability as the primary mechanism. The repository scripts remain useful for portable logical exports and migration between providers.

Do not commit `.dump` files to Git. The repository `.gitignore` should be extended for any custom backup directory you introduce outside the default `backups/` convention.
