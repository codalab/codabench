#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=/app/.env
TMP_FILE="${ENV_FILE}.tmp"

# read existing DJANGO_SECRET_KEY from .env (raw value after =)
existing=""
if [ -f "$ENV_FILE" ]; then
  existing=$(grep -E '^DJANGO_SECRET_KEY=' "$ENV_FILE" | tail -n1 | sed -E 's/^DJANGO_SECRET_KEY=//')
fi

# if variable is already provided by environment, persist it if absent from .env
if [ -n "${DJANGO_SECRET_KEY:-}" ]; then
  KEY="$DJANGO_SECRET_KEY"
  if [ -z "$existing" ]; then
    esc=$(printf '%s' "$KEY" | sed "s/'/'\\\\''/g")
    if [ -f "$ENV_FILE" ]; then
      grep -v -E '^DJANGO_SECRET_KEY=' "$ENV_FILE" > "$TMP_FILE" || true
    else
      : > "$TMP_FILE"
    fi
    printf "DJANGO_SECRET_KEY='%s'\n" "$esc" >> "$TMP_FILE"
    mv "$TMP_FILE" "$ENV_FILE"
  fi
  export DJANGO_SECRET_KEY="$KEY"
else
  if [ -n "$existing" ]; then
    # remove surrounding quotes if present
    KEY=$(printf '%s' "$existing" | sed -E "s/^'(.*)'$/\1/; s/^\"(.*)\"$/\1/")
    export DJANGO_SECRET_KEY="$KEY"
  else
    # generate, persist and export
    KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    esc=$(printf '%s' "$KEY" | sed "s/'/'\\\\''/g")
    if [ -f "$ENV_FILE" ]; then
      grep -v -E '^DJANGO_SECRET_KEY=' "$ENV_FILE" > "$TMP_FILE" || true
    else
      : > "$TMP_FILE"
    fi
    printf "DJANGO_SECRET_KEY='%s'\n" "$esc" >> "$TMP_FILE"
    mv "$TMP_FILE" "$ENV_FILE"
    export DJANGO_SECRET_KEY="$KEY"
  fi
fi

exec "$@"
