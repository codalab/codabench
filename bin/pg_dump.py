#!/usr/bin/env python3
"""
Usage, in `crontab -e`:

    @daily /home/ubuntu/competitions-v2/bin/pg_dump.py

"""
import time

from subprocess import check_output, PIPE, STDOUT

dump_name = time.strftime("%Y-%m-%d_%H-%M-%S.dump")

print(f"Making dump {dump_name}")

# Make dump
print(check_output([
    'docker-compose',
    'exec',
    'db',
    'bash',
    '-c',
    f'PGPASSWORD=$DB_PASSWORD pg_dump -Fc -U $DB_USER $DB_NAME > /app/backups/{dump_name}'
], stderr=STDOUT).decode())

# Push/destroy dump
print(check_output([
    'docker-compose', 'exec', 'django', 'python', 'manage.py', 'upload_backup', f'{dump_name}'
], stderr=STDOUT).decode())
