import os

from django.core.management.base import BaseCommand, CommandError

from utils.data import make_url_sassy, put_blob


class Command(BaseCommand):
    help = "Takes a database dump file and puts it on remote storage"

    def add_arguments(self, parser):
        parser.add_argument('backup_path', type=str, help='Path to backup to upload, relative to /app/backups/')

    def handle(self, *args, **options):
        backup_file_name = options['backup_path']
        backup_root = os.path.realpath("/app/backups")

        if os.path.isabs(backup_file_name):
            raise CommandError("backup_path must be relative to /app/backups")

        backup_path = os.path.realpath(os.path.join(backup_root, backup_file_name))
        if os.path.commonpath([backup_root, backup_path]) != backup_root:
            raise CommandError("backup_path must be relative to /app/backups")

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
