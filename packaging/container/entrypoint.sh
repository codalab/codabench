#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=/app/.env
TMP_FILE=${ENV_FILE}.tmp

if [ -z "${DJANGO_SECRET_KEY:-}" ]; then
  if [ -f "$ENV_FILE" ]; then
    existing=$(grep -E '^DJANGO_SECRET_KEY=' "$ENV_FILE" | tail -n1 | sed 's/^DJANGO_SECRET_KEY=//')
  else
    existing=""
  fi

  if [ -n "${existing:-}" ]; then
    export DJANGO_SECRET_KEY="$existing"
  else
    export DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    # persist: remove old DJANGO_SECRET_KEY lines and append the new one
    if [ -f "$ENV_FILE" ]; then
      grep -v -E '^DJANGO_SECRET_KEY=' "$ENV_FILE" > "$TMP_FILE" || true
    else
      : > "$TMP_FILE"
    fi
    printf "%s\n" "DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY" >> "$TMP_FILE"
    mv "$TMP_FILE" "$ENV_FILE"
  fi
fi

exec "$@"
