#!/usr/bin/env bash

set -euo pipefail

usage() {
	cat <<'EOF'
Usage: deploy_compose_release.sh CURRENT_IMAGE RELEASE_IMAGE

Required environment variables:
  SITE_NAME          Site to back up before migration.

Optional environment variables:
  COMPOSE_FILE       Compose file to update (default: ./frappe-compose.yml).
  COMPOSE_PROJECT    Compose project name (default: frappe).
  BACKUP_ROOT        Backup directory (default: ./backups).
  DB_HOST_OVERRIDE   Database host reachable from the deployment host.
  HEALTH_URL         URL that must return a successful HTTP status after deployment.
  EXPECTED_APP       App whose installed version should be checked after deployment.
  EXPECTED_VERSION   Expected version for EXPECTED_APP.
  APP_SERVICES       Space-separated services to recreate.
EOF
}

if [ "$#" -ne 2 ] || [ -z "${SITE_NAME:-}" ]; then
	usage >&2
	exit 2
fi

current_image=$1
release_image=$2
compose_file=${COMPOSE_FILE:-./frappe-compose.yml}
compose_project=${COMPOSE_PROJECT:-frappe}
backup_root=${BACKUP_ROOT:-./backups}
app_services=${APP_SERVICES:-backend websocket queue-short queue-long scheduler frontend}

if [ ! -f "$compose_file" ]; then
	echo "Compose file not found: $compose_file" >&2
	exit 1
fi

command -v docker >/dev/null
command -v pg_dump >/dev/null
command -v psql >/dev/null
command -v python3 >/dev/null

compose() {
	docker compose -p "$compose_project" -f "$compose_file" "$@"
}

lock_file="/tmp/${compose_project}-release.lock"
exec 9>"$lock_file"
if ! flock -n 9; then
	echo "Another release is already running for $compose_project" >&2
	exit 1
fi

started_at=$SECONDS
stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup_dir="$backup_root/${SITE_NAME}-before-${stamp}"
candidate_file="${compose_file}.candidate-${stamp}"
backend_container=$(compose ps -q backend)

if [ -z "$backend_container" ]; then
	echo "The backend service is not running" >&2
	exit 1
fi

mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
cp "$compose_file" "$backup_dir/frappe-compose.yml"

site_root="/home/frappe/frappe-bench/sites/$SITE_NAME"
site_config=$(docker exec "$backend_container" cat "$site_root/site_config.json")
common_config=$(docker exec "$backend_container" cat /home/frappe/frappe-bench/sites/common_site_config.json)

json_value() {
	local key=$1
	local fallback=${2:-}
	SITE_CONFIG="$site_config" COMMON_CONFIG="$common_config" KEY="$key" FALLBACK="$fallback" \
		python3 - <<'PY'
import json
import os

site = json.loads(os.environ["SITE_CONFIG"])
common = json.loads(os.environ["COMMON_CONFIG"])
key = os.environ["KEY"]
fallback = os.environ["FALLBACK"]
value = site.get(key, common.get(key, fallback))
print(value if value is not None else "")
PY
}

db_name=$(json_value db_name)
db_user=$(json_value db_user "$db_name")
db_password=$(json_value db_password)
db_host=${DB_HOST_OVERRIDE:-$(json_value db_host 127.0.0.1)}
db_port=$(json_value db_port 5432)

if [ -z "$db_name" ] || [ -z "$db_user" ] || [ -z "$db_password" ]; then
	echo "Database credentials are incomplete for $SITE_NAME" >&2
	exit 1
fi

server_version=$(PGPASSWORD="$db_password" psql \
	--host "$db_host" \
	--port "$db_port" \
	--username "$db_user" \
	--dbname "$db_name" \
	--tuples-only \
	--no-align \
	--command "show server_version_num")
server_major=$((server_version / 10000))
dump_major=$(pg_dump --version | sed -E 's/.* ([0-9]+)(\..*)?$/\1/')
if [ "$dump_major" -lt "$server_major" ]; then
	echo "pg_dump $dump_major cannot back up PostgreSQL $server_major" >&2
	exit 1
fi

echo "Backing up $SITE_NAME to $backup_dir"
PGPASSWORD="$db_password" pg_dump \
	--host "$db_host" \
	--port "$db_port" \
	--username "$db_user" \
	--format custom \
	--file "$backup_dir/database.dump" \
	"$db_name"
docker exec "$backend_container" tar -czf - -C "$site_root" \
	public/files private/files site_config.json >"$backup_dir/site-files-and-config.tar.gz"
(
	cd "$backup_dir"
	sha256sum database.dump site-files-and-config.tar.gz frappe-compose.yml >SHA256SUMS
	sha256sum -c SHA256SUMS
)

echo "Pulling $release_image"
docker pull "$release_image"
docker run --rm --entrypoint bench "$release_image" version

CURRENT_IMAGE="$current_image" RELEASE_IMAGE="$release_image" \
	python3 - "$compose_file" "$candidate_file" <<'PY'
import os
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
current = os.environ["CURRENT_IMAGE"]
release = os.environ["RELEASE_IMAGE"]
content = source.read_text(encoding="utf-8")
count = content.count(current)
if not count:
    raise SystemExit(f"Current image not found in compose file: {current}")
target.write_text(content.replace(current, release), encoding="utf-8")
print(f"Updated {count} image references")
PY

docker compose -p "$compose_project" -f "$candidate_file" config --quiet

echo "Migrating sites with $release_image"
docker compose -p "$compose_project" -f "$candidate_file" run \
	--rm \
	--no-deps \
	--pull never \
	backend bench --site all migrate

mv "$candidate_file" "$compose_file"

echo "Recreating application services: $app_services"
# shellcheck disable=SC2086
compose up -d --no-deps --force-recreate --pull never $app_services
compose exec -T backend bench --site "$SITE_NAME" clear-cache

if [ -n "${EXPECTED_APP:-}" ]; then
	actual_version=$(compose exec -T backend bench version | awk -v app="$EXPECTED_APP" '$1 == app { print $2 }')
	if [ -z "$actual_version" ] || { [ -n "${EXPECTED_VERSION:-}" ] && [ "$actual_version" != "$EXPECTED_VERSION" ]; }; then
		echo "Unexpected $EXPECTED_APP version: ${actual_version:-missing}" >&2
		exit 1
	fi
	echo "$EXPECTED_APP version: $actual_version"
fi

if [ -n "${HEALTH_URL:-}" ]; then
	status=""
	for _ in $(seq 1 30); do
		status=$(curl -sS -o /tmp/frappe-release-health-body -w "%{http_code}" "$HEALTH_URL" || true)
		if [ "$status" -ge 200 ] 2>/dev/null && [ "$status" -lt 400 ]; then
			break
		fi
		sleep 2
	done
	if [ -z "$status" ] || [ "$status" -lt 200 ] || [ "$status" -ge 400 ]; then
		echo "Health check failed with HTTP ${status:-unknown}: $HEALTH_URL" >&2
		exit 1
	fi
	echo "Health check passed: HTTP $status"
fi

compose ps
echo "Backup: $backup_dir"
echo "Release completed in $((SECONDS - started_at)) seconds"
