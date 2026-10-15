#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source /etc/os-release
case "$ID" in
debian | ubuntu) ;;
*)
  echo "SQL Server ODBC installation requires Debian or Ubuntu, got: $ID" >&2
  exit 1
  ;;
esac

export DEBIAN_FRONTEND=noninteractive
if ! command -v curl >/dev/null; then
  apt-get update
  apt-get install -y --no-install-recommends ca-certificates curl
fi

repo_package="$(mktemp --suffix=.deb)"
trap 'rm -f "$repo_package"' EXIT
curl --fail --show-error --location --retry 3 --connect-timeout 30 --max-time 120 \
  "https://packages.microsoft.com/config/$ID/$VERSION_ID/packages-microsoft-prod.deb" \
  --output "$repo_package"
dpkg -i "$repo_package"
apt-get update
ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 libgssapi-krb5-2
odbcinst -q -d -n "ODBC Driver 18 for SQL Server"
rm -rf /var/lib/apt/lists/*
