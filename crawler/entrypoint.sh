#!/bin/bash

set -e

export PGUSER=$(whoami)

# Check variables
if [[ -z "$PGDATA" || -z "$PG_PORT" || -z "$PGBOUNCER_PORT" || -z "$PGUSER" ]]; then
  echo "Missing required environment variables."
  exit 1
fi

mkdir -p "$PGDATA"
if [ "$(id -u)" = "0" ]; then
  chown -R postgres:postgres "$PGDATA"
fi
chmod 700 "$PGDATA"

# 1. Mount pg_wal to tmpfs
TMP_WAL_DIR="${TMP_WAL_BASE:-/dev/shm}/${WALDATA:-pg_wal_default}"
mkdir -p "$TMP_WAL_DIR"
if [ "$(id -u)" = "0" ]; then
  chown postgres:postgres "$TMP_WAL_DIR"
fi
chmod 700 "$TMP_WAL_DIR"

# 2. Set permanent WAL archive directory under PGDATA
ARCHIVE_DIR="${ARCHIVE_PATH:-$PGDATA/wal_archive}"
mkdir -p "$ARCHIVE_DIR"
if [ "$(id -u)" = "0" ]; then
  chown postgres:postgres "$ARCHIVE_DIR"
fi
chmod 700 "$ARCHIVE_DIR"

# Create PostgreSQL lock file directory
if [ "$(id -u)" = "0" ]; then
  mkdir -p /var/run/postgresql
  chmod 777 /var/run/postgresql
fi

# Initialize database (if not initialized)
if [ ! -f "$PGDATA/PG_VERSION" ]; then
  # Clean any metadata files injected by Docker Desktop on macOS (VirtioFS artifacts)
  # Safe because the absence of PG_VERSION means there is no valid database here
  find "${PGDATA}" -mindepth 1 -delete 2>/dev/null || true
  /usr/lib/postgresql/*/bin/initdb -D "$PGDATA" --username="$PGUSER" --waldir="$TMP_WAL_DIR"
else
  echo "PostgreSQL Exisiting, skip initdb"
fi

# Configure PostgreSQL, only append if config does not exist
POSTGRESQL_CONF="$PGDATA/postgresql.conf"
if ! grep -q "^listen_addresses" "$POSTGRESQL_CONF"; then
  cat >> "$POSTGRESQL_CONF" <<EOF
listen_addresses = '*'
port = $PG_PORT
max_connections = 2000
shared_buffers = 64GB
work_mem = 16MB
effective_cache_size = 128GB
maintenance_work_mem = 2GB
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB
synchronous_commit = off    # Performance boost but increases data loss risk
wal_writer_delay = 200ms    # Balance write delay
wal_compression = on
max_wal_size = 16GB
checkpoint_timeout = 30min
checkpoint_completion_target = 0.9
archive_mode = off
archive_timeout = 5min
archive_command = 'test ! -f "$ARCHIVE_DIR/%f" && cp %p "$ARCHIVE_DIR/%f"'
restore_command = 'cp "$ARCHIVE_DIR/%f" %p'
EOF
else
  echo "PostgreSQL Existing, skip postgresql.conf setting"
fi

# Configure pg_hba.conf
PG_HBA_CONF="$PGDATA/pg_hba.conf"
if ! grep -q "0.0.0.0/0" "$PG_HBA_CONF"; then
  cat >> "$PG_HBA_CONF" <<EOF
host    all             all             0.0.0.0/0               md5
host    all             all             ::0/0                   md5
local   all             all                                     trust
EOF
else
  echo "pg_hba.conf existing, skip setting"
fi

# Start PostgreSQL
if /usr/lib/postgresql/*/bin/pg_ctl -D "$PGDATA" status > /dev/null 2>&1; then
  echo "PostgreSQL already running, attempting to stop it first..."
  # Attempt fast shutdown. If fails, it might not be running or is stuck.
  /usr/lib/postgresql/*/bin/pg_ctl -D "$PGDATA" -o "-m fast" stop || echo "Stop command issued or PostgreSQL was not running. Continuing..."
  sleep 5 # Give the server time to shut down
fi

# If postmaster.pid exists and service is not running, clean it
if [ -f "$PGDATA/postmaster.pid" ]; then
    if ! /usr/lib/postgresql/*/bin/pg_ctl -D "$PGDATA" status > /dev/null 2>&1; then
        echo "Removing stale postmaster.pid file."
        rm -f "$PGDATA/postmaster.pid"
    else
        echo "PostgreSQL appears to be running, not removing postmaster.pid."
    fi
fi

echo "Starting PostgreSQL..."
/usr/lib/postgresql/*/bin/pg_ctl -D "$PGDATA" -l "$PGDATA/logfile" start || {
  echo "PostgreSQL Start Failed, check log:"
  cat "$PGDATA/logfile"
  exit 1
}

# Wait for PostgreSQL to become ready to listen
echo "Waiting for PostgreSQL to become ready..."
for i in {1..30}; do # Increase retries from 10 to 30
  if pg_isready -h 127.0.0.1 -p "$PG_PORT" -U "$PGUSER"; then
    echo "PostgreSQL is ready."
    break
  else
    echo "Still waiting for PostgreSQL (attempt $i/30)..."
    sleep 3 # Increase wait time from 2 to 3 seconds
  fi
done

# Timeout detection
if ! pg_isready -h 127.0.0.1 -p "$PG_PORT" -U "$PGUSER"; then
  echo "PostgreSQL did not become ready in time. Exiting."
  cat "$PGDATA/logfile"
  exit 1
fi

# Set database user password (strong password by default)
psql -h 127.0.0.1 -p "$PG_PORT" -U "$PGUSER" -d postgres -c "ALTER ROLE \"$PGUSER\" WITH PASSWORD 'strongpassword';"

# Create sites database (if not exists)
DB_EXISTS=$(psql -h 127.0.0.1 -p "$PG_PORT" -U "$PGUSER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'sites'")
if [[ "$DB_EXISTS" != "1" ]]; then
  psql -h 127.0.0.1 -p "$PG_PORT" -U "$PGUSER" -d postgres -c "CREATE DATABASE sites"
fi

# Configure PgBouncer
mkdir -p /etc/pgbouncer
cat > /etc/pgbouncer/pgbouncer.ini <<EOF
[databases]
postgres = host=127.0.0.1 port=$PG_PORT dbname=postgres user=$PGUSER password=strongpassword
sites = host=127.0.0.1 port=$PG_PORT dbname=sites user=$PGUSER password=strongpassword

[pgbouncer]
listen_addr = *
listen_port = $PGBOUNCER_PORT
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
admin_users = postgres, $PGUSER
pool_mode = transaction
max_client_conn = 20000
default_pool_size = 300
min_pool_size = 50
reserve_pool_size = 100
log_connections = 1
log_disconnections = 1
pidfile = /var/run/pgbouncer/pgbouncer.pid
EOF

echo "\"$PGUSER\" \"strongpassword\"" > /etc/pgbouncer/userlist.txt

# Start PgBouncer
mkdir -p /var/run/pgbouncer
PGBOUNCER_PID_FILE="/var/run/pgbouncer/pgbouncer.pid"

# Check if PgBouncer is already running
if [ -f "$PGBOUNCER_PID_FILE" ] && kill -0 $(cat "$PGBOUNCER_PID_FILE") 2>/dev/null; then
  echo "PgBouncer already running. Skip"
else
  echo "Start PgBouncer..."
  pgbouncer -d /etc/pgbouncer/pgbouncer.ini || {
    echo "PgBouncer Failed"
    exit 1
  }
fi

# crawler Check variables
if [[ -z "$CRAWLER_ID" ]]; then
  echo "Missing required environment (CRAWLER_ID) variables."
  exit 1
fi

# add sites to database
cd /app/src
CSV_FILE=${CSV_FILE:-example.csv}
python3 source_tranco_async.py --csv "$CSV_FILE"

cd /app

if [[ -z "$ZMQ_HOST" ]]; then
  echo "Missing required environment (ZMQ_HOST) variables."
  exit 1
fi

# Check if using IPC protocol
if [[ "$ZMQ_HOST" == ipc://* ]]; then
  # Extract socket file path
  SOCKET_PATH=${ZMQ_HOST#ipc://}
  
  # Create directory
  SOCKET_DIR=$(dirname "$SOCKET_PATH")
  mkdir -p "$SOCKET_DIR"
  
  # Set permissions
  chmod 777 "$SOCKET_DIR"
  
  # Delete old socket file if exists
  if [ -e "$SOCKET_PATH" ]; then
    rm "$SOCKET_PATH"
  fi
  
  echo "Prepared socket path for ZMQ IPC protocol: $SOCKET_PATH"
fi

cd /app/crawlerserver

mkdir -p /etc/supervisor/conf.d
cat > /etc/supervisor/conf.d/zmq_server.conf <<EOF
[program:zmq_server]
command=python3 /app/crawlerserver/src/zmq_server.py
directory=/app/crawlerserver/src
autostart=true
autorestart=false
stderr_logfile=/var/log/zmq_server.err.log
stdout_logfile=/var/log/zmq_server.out.log
EOF

# Start Supervisor and load config
supervisord -c /etc/supervisor/supervisord.conf
supervisorctl reread
supervisorctl update

# config the tscrawler
cd /app/tscrawler

cd src/snippets/cxss/persistent-clientside-xss/src/
pip install -r requirements.txt

## Add .env file
cd /app/tscrawler/src
cat > .env <<EOF
# Experiment to run (set to cxss to start client-side XSS experiment)
EXPERIMENT=cxss

# crawler setting
CRAWLER_ID=0
CRAWLER_START=1     # Id of first crawler to start
CRAWLER_COUNT=50     # Number of seperate crawlers to start (max. cap on crawler id, incremented during start)
POLLING_INTERVAL=2  # Interval crawlers look into database for new tasks in seconds

# ZMQ Configuration for account framework interaction
ZMQ_ENABLE=true
ZMQ_HOST=$ZMQ_HOST
ZMQ_EXPERIMENT=cxss # ZMQ_EXPERIMENT must same to the EXPERIMENT

# Starting insecure webserver containing vulnerable page examples (for use without ZMQ)
START_INSECURE_WEBSERVER=false

# Database configuration details
POSTGRES_HOST=127.0.0.1
POSTGRES_USER=$PGUSER
POSTGRES_PASSWORD=strongpassword
POSTGRES_PORT=$PG_PORT
PGBOUNCER_PORT=$PGBOUNCER_PORT

PM2_HOME=/tmp/my_new_pm2_dir/$PGDATA

# Database

EOF

export PM2_HOME=/tmp/my_new_pm2_dir/$PGDATA

# update ulimit
ulimit -n 65535

# move into the /run
cd /run
cp -r /app/tscrawler/ ./

# Keep container running in foreground so Docker doesn't exit
# Tails the PostgreSQL log so output is visible via 'docker logs'
tail -f "$PGDATA/logfile"
