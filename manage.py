#!/usr/bin/env python
import sys
import os
import subprocess

if __name__ == "__main__":
    sys.path.append('src')
    settings_module = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')

    if 'runserver' in sys.argv:
        print("npm-watching")
        subprocess.Popen(["npm-watch"])

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
