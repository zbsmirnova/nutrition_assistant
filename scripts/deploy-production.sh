#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_SHA:?GITHUB_SHA is required}"
: "${DEPLOY_HOST:?DEPLOY_HOST is required}"
: "${DEPLOY_USER:?DEPLOY_USER is required}"
: "${DEPLOY_SSH_KEY_FILE:?DEPLOY_SSH_KEY_FILE is required}"
: "${DEPLOY_KNOWN_HOSTS_FILE:?DEPLOY_KNOWN_HOSTS_FILE is required}"

deploy_port="${DEPLOY_SSH_PORT:-22}"
workspace="${GITHUB_WORKSPACE:-$(pwd)}"
temporary_dir="${RUNNER_TEMP:-/tmp}"
archive="$temporary_dir/nutrition_assistant-${GITHUB_SHA}.tar.gz"
remote_archive="/tmp/nutrition_assistant-${GITHUB_SHA}.tar.gz"

tar --exclude-vcs \
    --exclude='.env' \
    --exclude='.env.*' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    -czf "$archive" -C "$workspace" .

ssh_options=(
  -i "$DEPLOY_SSH_KEY_FILE"
  -o IdentitiesOnly=yes
  -o BatchMode=yes
  -o StrictHostKeyChecking=yes
  -o UserKnownHostsFile="$DEPLOY_KNOWN_HOSTS_FILE"
  -p "$deploy_port"
)
scp_options=(
  -i "$DEPLOY_SSH_KEY_FILE"
  -o IdentitiesOnly=yes
  -o BatchMode=yes
  -o StrictHostKeyChecking=yes
  -o UserKnownHostsFile="$DEPLOY_KNOWN_HOSTS_FILE"
  -P "$deploy_port"
)

scp "${scp_options[@]}" "$archive" "$DEPLOY_USER@$DEPLOY_HOST:$remote_archive"

ssh "${ssh_options[@]}" "$DEPLOY_USER@$DEPLOY_HOST" \
  "GITHUB_SHA='$GITHUB_SHA' bash -s" <<'REMOTE'
set -euo pipefail

app_root=/opt/nutrition_assistant
archive="/tmp/nutrition_assistant-${GITHUB_SHA}.tar.gz"
release_dir="$app_root/releases/$GITHUB_SHA"

test -f "$app_root/.env"
install -d -m 0755 "$app_root/releases"
rm -rf "$release_dir"
install -d -m 0755 "$release_dir"
tar -xzf "$archive" -C "$release_dir"

compose=(docker compose --project-name nutrition_assistant \
  --env-file "$app_root/.env" \
  -f "$release_dir/compose.production.yml")

"${compose[@]}" config --quiet
"${compose[@]}" up -d db
"${compose[@]}" build migrate worker
"${compose[@]}" run --rm migrate
"${compose[@]}" up -d --no-deps --force-recreate worker

worker_id=""
health="unknown"
for _ in $(seq 1 30); do
  worker_id=$("${compose[@]}" ps -q worker 2>/dev/null || true)
  if [ -n "$worker_id" ]; then
    health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$worker_id" 2>/dev/null || true)
    if [ "$health" = "healthy" ]; then
      break
    fi
  fi
  sleep 2
done

if [ "$health" != "healthy" ]; then
  "${compose[@]}" ps
  "${compose[@]}" logs --tail=80 worker || true
  exit 1
fi

"${compose[@]}" ps
rm -f "$archive"
REMOTE

rm -f "$archive"
