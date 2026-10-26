#!/usr/bin/env bash
#
# db_restore.sh — restore the CodeSense postgres database from a backup file
# produced by db_backup.sh. Usage: db_restore.sh <backup-file>
set -euo pipefail

BACKUP_FILE="${1:?Usage: db_restore.sh <backup-file>}"

[[ -f "$BACKUP_FILE" ]] || {
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
}

POSTGRES_SERVER="${POSTGRES_SERVER:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-codesense}"

export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
  -h "$POSTGRES_SERVER" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 \
  -f "$BACKUP_FILE"

unset PGPASSWORD

echo "Restored from $BACKUP_FILE"
