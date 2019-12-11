#!/usr/bin/env python
import sys
import os
import subprocess

if __name__ == "__main__":
    sys.path.append('src')
    settings_module = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.develop')

    if 'runserver' in sys.argv:
        subprocess.Popen(["npm-watch"])

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
