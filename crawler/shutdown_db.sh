#!/bin/bash
set -e

export PM2_HOME=/tmp/my_pm2_dir
export PGUSER=${PGUSER:-$(whoami)}

bash experiment-stop.sh

# Safely terminate PgBouncer
if pgrep -f pgbouncer > /dev/null; then
  echo "Stopping PgBouncer..."
  pkill -INT pgbouncer
  sleep 2
else
  echo "PgBouncer not running."
fi

# Stop PostgreSQL
echo "Stopping PostgreSQL safely with fast shutdown..."
/usr/lib/postgresql/*/bin/pg_ctl -D "$PGDATA" -m fast stop

# Verify if stopped successfully
sleep 2
if ! /usr/lib/postgresql/*/bin/pg_ctl -D "$PGDATA" status > /dev/null 2>&1; then
  echo "✅ PostgreSQL stopped."
else
  echo "⚠️ PostgreSQL still running."
fi

# Clean up stale pid
if [ -f "$PGDATA/postmaster.pid" ]; then
  echo "Checking postmaster.pid..."
  if ! /usr/lib/postgresql/*/bin/pg_ctl -D "$PGDATA" status > /dev/null 2>&1; then
    echo "Removing stale postmaster.pid..."
    rm -f "$PGDATA/postmaster.pid"
  fi
fi

# Copy pg_wal to secure directory
if [[ -n "$WALDATA" ]]; then
  TMP_WAL_DIR="/dev/shm/$WALDATA"
  BACKUP_DIR="/home/worker/persisted_wal/$WALDATA"

  echo "Backing up WAL from $TMP_WAL_DIR to $BACKUP_DIR..."

  if [ -d "$TMP_WAL_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    cp -a "$TMP_WAL_DIR/." "$BACKUP_DIR/"
    echo "✅ WAL successfully backed up to $BACKUP_DIR"
  else
    echo "❌ WAL directory $TMP_WAL_DIR not found — nothing to back up."
  fi
else
  echo "⚠️ WALDATA variable not set — cannot back up WAL."
fi
