#!/usr/bin/env bash
# Run a throwaway local Postgres cluster WITHOUT Docker.
#
# This is a fallback for environments where the Docker registry is unreachable.
# The supported developer path is `docker compose up -d db` (see docker-compose.yml);
# this script mirrors the same database/role/password so .env works unchanged.
set -euo pipefail

PGBIN=/usr/lib/postgresql/16/bin
PGDATA=${PGDATA:-/tmp/askrevenue-pgdata}
PGPORT=${PGPORT:-5432}

# Postgres refuses to run as root. If invoked as root, drop to the postgres OS user
# for the server processes (initdb/pg_ctl); psql connects over TCP and is fine as-is.
if [ "$(id -u)" = "0" ]; then
  RUN="su postgres -c"
  # Only create-and-chown the data dir on first init; afterwards leave it alone
  # so we don't reset perms (postgres rejects anything other than 0700/0750).
  if [ ! -d "$PGDATA" ]; then
    install -d -m 700 -o postgres -g postgres "$PGDATA"
  fi
else
  RUN="bash -c"
fi

start() {
  if [ ! -d "$PGDATA/base" ]; then
    echo "initdb -> $PGDATA"
    $RUN "'$PGBIN/initdb' -D '$PGDATA' -U postgres --auth-local=trust --auth-host=trust" >/dev/null
    echo "listen_addresses = 'localhost'" >> "$PGDATA/postgresql.conf"
    echo "port = $PGPORT" >> "$PGDATA/postgresql.conf"
  fi
  # Clear any stale pid lock from an unclean prior shutdown, then start
  # detached via setsid so the server is parented to init and survives the
  # shell that launched it (essential in container/sandbox environments).
  rm -f "$PGDATA/postmaster.pid"
  chmod 700 "$PGDATA"
  $RUN "setsid '$PGBIN/postgres' -D '$PGDATA' >>'$PGDATA/server.log' 2>&1 < /dev/null &"
  # Wait for the server to accept connections.
  for _ in $(seq 1 30); do
    if "$PGBIN/pg_isready" -h localhost -p "$PGPORT" >/dev/null 2>&1; then break; fi
    sleep 0.5
  done
  bootstrap
}

bootstrap() {
  # Create the owning role + database to match docker-compose.yml, idempotently.
  "$PGBIN/psql" -U postgres -h localhost -p "$PGPORT" -d postgres -v ON_ERROR_STOP=1 <<'SQL'
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='askrevenue') THEN
    CREATE ROLE askrevenue LOGIN SUPERUSER PASSWORD 'askrevenue';
  END IF;
END $$;
SELECT 'CREATE DATABASE askrevenue OWNER askrevenue'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='askrevenue')\gexec
SQL
  # Apply the read-only role provisioning (same SQL Docker would run on init).
  "$PGBIN/psql" -U postgres -h localhost -p "$PGPORT" -d askrevenue -v ON_ERROR_STOP=1 \
    -f "$(dirname "$0")/../infra/db-init/01-readonly-role.sql"
  echo "Local Postgres ready on port $PGPORT (db=askrevenue, user=askrevenue)."
}

stop() {
  if [ -f "$PGDATA/postmaster.pid" ]; then
    $RUN "'$PGBIN/pg_ctl' -D '$PGDATA' -m fast -w stop" || true
  fi
}

case "${1:-start}" in
  start) start ;;
  stop) stop ;;
  bootstrap) bootstrap ;;
  *) echo "usage: $0 {start|stop|bootstrap}"; exit 1 ;;
esac
