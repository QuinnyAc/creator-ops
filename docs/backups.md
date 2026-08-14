# PostgreSQL Backup and Restore

Creator Ops stores creator workflow data in PostgreSQL. A self-hosted deployment is not production-ready unless the database is backed up and the restore path is tested.

## Backup the development stack

With the normal Docker Compose stack running:

```bash
make backup
```

The default output is a timestamped PostgreSQL custom-format dump:

```text
backups/creator-ops-YYYYMMDDTHHMMSSZ.dump
```

The backup script writes to a temporary `.partial` file and only renames it to the final path after `pg_dump` succeeds and produces non-empty output. Failed backups therefore do not leave a file that looks complete.

Choose an explicit output path when needed:

```bash
./scripts/backup-postgres.sh /secure/path/creator-ops.dump
```

The script runs `pg_dump` inside the database container and reads `POSTGRES_USER` / `POSTGRES_DB` from that container, avoiding duplicated credentials on the command line.

## Backup the production Compose stack

```bash
CREATOR_OPS_COMPOSE_FILE=docker-compose.prod.yml \
CREATOR_OPS_ENV_FILE=.env.production \
CREATOR_OPS_BACKUP_DIR=/srv/creator-ops/backups \
./scripts/backup-postgres.sh
```

Store production backup files outside the application checkout and preferably copy them to a separate failure domain.

## Restore

Restore is deliberately guarded because it replaces current PostgreSQL data. On a production deployment, schedule the operation inside a maintenance window and verify the backup file before beginning.

Development convenience target:

```bash
make restore BACKUP=backups/creator-ops-20260814T120000Z.dump
```

Direct script usage requires explicit confirmation:

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

1. verifies the dump exists and is non-empty;
2. refuses to continue without `CREATOR_OPS_RESTORE_CONFIRM=YES`;
3. stops `api` and `web` so application writes cannot race the restore;
4. drops and recreates the PostgreSQL `public` schema;
5. restores the custom-format dump into that clean schema;
6. restarts API and Web on exit;
7. lets normal API startup apply any Alembic migrations newer than the restored database.

Resetting the schema is important when restoring an older backup onto a newer installation. `pg_restore --clean` alone only knows about objects present in the dump; objects introduced after the backup could otherwise survive and conflict with migrations.

## CI restore proof

`.github/workflows/backup-restore-smoke.yml` exercises the actual scripts against an ephemeral Creator Ops Docker/PostgreSQL stack on pull requests.

The smoke test:

1. boots the application and database;
2. creates a marker row;
3. takes a real custom-format backup;
4. deletes the backed-up marker and creates a new post-backup table;
5. restores the backup through `restore-postgres.sh`;
6. verifies the original marker returned;
7. verifies the post-backup table did **not** survive.

This protects both data restoration and clean historical-state semantics.

## Recommended production policy

At minimum:

- create automated daily backups;
- keep multiple historical copies;
- store at least one copy outside the Creator Ops host;
- encrypt storage containing real creator/customer data;
- restrict access to operators who need it;
- monitor backup job failures;
- test restore on a disposable environment on a recurring schedule.

A backup that has never been restored is only an assumption.

## Managed PostgreSQL

When using a managed PostgreSQL provider, prefer its native automated backup and point-in-time recovery as the primary recovery mechanism. These repository scripts remain useful for portable logical exports, disaster-recovery exercises, and provider migration.

Do not commit `.dump` files to Git. The default `backups/` path and `*.dump` are ignored by the repository.
