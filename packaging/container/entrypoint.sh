#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=/.env

existing=""
if [ -f "$ENV_FILE" ]; then
  existing=$(grep -E '^SECRET_KEY=' "$ENV_FILE" | tail -n1 | sed -E 's/^SECRET_KEY=//')
fi

if [ -n "${SECRET_KEY:-}" ]; then
  KEY="$SECRET_KEY"
  if [ -z "$existing" ]; then
    esc=$(printf '%s' "$KEY" | sed "s/'/'\\\\''/g")
    if [ -f "$ENV_FILE" ]; then
      TMP=$(mktemp)
      grep -v -E '^SECRET_KEY=' "$ENV_FILE" > "$TMP" || true
    else
      TMP=$(mktemp)
      : > "$TMP"
    fi
    printf "SECRET_KEY='%s'\n" "$esc" >> "$TMP"
    mv "$TMP" "$ENV_FILE"
  fi
  export SECRET_KEY="$KEY"
else
  if [ -n "$existing" ]; then
    KEY=$(printf '%s' "$existing" | sed -E "s/^'(.*)'$/\1/; s/^\"(.*)\"$/\1/")
    export SECRET_KEY="$KEY"
  else
    KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    esc=$(printf '%s' "$KEY" | sed "s/'/'\\\\''/g")
    if [ -f "$ENV_FILE" ]; then
      TMP=$(mktemp)
      grep -v -E '^SECRET_KEY=' "$ENV_FILE" > "$TMP" || true
    else
      TMP=$(mktemp)
      : > "$TMP"
    fi
    printf "SECRET_KEY='%s'\n" "$esc" >> "$TMP"
    mv "$TMP" "$ENV_FILE"
    export SECRET_KEY="$KEY"
  fi
fi

exec "$@"
