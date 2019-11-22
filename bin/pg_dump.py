#!/usr/bin/env python3
"""
Usage, in `crontab -e`:

    @daily /home/ubuntu/competitions-v2/scripts/pg_dump.py

"""
import time

from subprocess import call


dump_name = time.strftime("%Y-%m-%d_%H-%M-%S.dump")

print(f"Making dump {dump_name}")

# Make dump
call([
    'docker-compose',
    'exec',
    'db',
    'bash',
    '-c',
    f'PGPASSWORD=$DB_PASSWORD pg_dump -Fc -U $DB_USER $DB_NAME > /app/backups/{dump_name}'
])

# Push/destroy dump
call([
    'docker-compose', 'exec', 'django', 'python', 'manage.py', 'upload_backup', f'{dump_name}'
])
