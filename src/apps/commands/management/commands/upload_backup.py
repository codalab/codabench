from os import remove
from os.path import join

from django.core.management.base import BaseCommand

from utils.data import make_url_sassy, put_blob


class Command(BaseCommand):
    help = "Takes a database dump file and puts it on remote storage"

    def add_arguments(self, parser):
        parser.add_argument('backup_path', type=str, help='Path to backup to upload, relative to /app/backups/')

    def handle(self, *args, **options):
        backup_file_name = options['backup_path']
        backup_path = join("/app/backups", options['backup_path'])

        # Upload it
        print("Uploading backup '{}'".format(backup_path))
        upload_url = make_url_sassy('backups/{}'.format(backup_file_name), permission='w', content_type=None)
        resp = put_blob(upload_url, backup_path)

        if resp.status_code == 200:
            print("Success! Removing local dump file '{}'".format(backup_path))
        else:
            print(f"FAILED TO SEND! Status code: {resp.status_code}\n{resp.content}")

        # Clean up
        remove(backup_path)
