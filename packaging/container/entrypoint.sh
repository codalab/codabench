#!/bin/bash
set -e

# Générer la clé Django si elle n'existe pas
if [ -z "$DJANGO_SECRET_KEY" ]; then
    export DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
fi

# Exécuter la commande passée au conteneur (migrate, collectstatic, watchmedo…)
exec "$@"
