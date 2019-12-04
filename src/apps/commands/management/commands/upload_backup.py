import os

from django.core.management.base import BaseCommand

from utils.data import make_url_sassy, put_blob


class Command(BaseCommand):
    help = "Takes a database dump file and puts it on remote storage"

    def add_arguments(self, parser):
        parser.add_argument('backup_path', type=str, help='Path to backup to upload, relative to /app/backups/')

    def handle(self, *args, **options):
        backup_file_name = options['backup_path']
        backup_path = os.path.join("/app/backups", options['backup_path'])

        # Upload it
        upload_url = make_url_sassy(
            f'backups/{backup_file_name}',
            permission='w',
            content_type=None
        )
        print(f"Uploading backup '{backup_path}' to '{upload_url}'")
        resp = put_blob(upload_url, backup_path)

        if resp.status_code == 200:
            print(f"Success!")
        else:
            print(f"FAILED TO SEND! Result ({resp.status_code}):\n{resp.content}")

        # Clean up
        print(f"Removing local dump file '{backup_path}'")
        os.remove(backup_path)
