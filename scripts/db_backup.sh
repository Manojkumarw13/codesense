#!/usr/bin/env bash
#
# db_backup.sh — pg_dump the CodeSense postgres database to a timestamped
# backup file. Run where postgresql-client is installed (e.g. the backend
# container or a backup host). All settings are overridable via environment
# variables matching docker-compose / .env.
set -euo pipefail

POSTGRES_SERVER="${POSTGRES_SERVER:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-codesense}"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/codesense_$(date +%Y%m%d_%H%M%S).sql"

export PGPASSWORD="$POSTGRES_PASSWORD"

pg_dump \
  -h "$POSTGRES_SERVER" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --clean --if-exists \
  > "$BACKUP_FILE"

unset PGPASSWORD

echo "Backup written to $BACKUP_FILE"
