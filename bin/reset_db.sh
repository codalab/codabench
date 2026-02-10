#!/usr/bin/env bash

docker compose exec db bash -c "
echo 'dropping database'
dropdb --if-exists -U \$DB_USERNAME \$DB_NAME &&
echo \$DB_PASSWORD &&
echo 'drop successful'
echo 'creating db'
createdb -U \$DB_USERNAME \$DB_NAME &&
echo 'create successful'
exit" &&

docker compose exec django bash -c "
python manage.py migrate &&
python manage.py generate_data
exit"
