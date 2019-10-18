import datetime
import logging
import os
import shutil

from dateutil import parser
from django.core.files import File
from django.utils import timezone

from datasets.models import Data
from competitions.unpacker.exceptions import CompetitionUnpackingException

logger = logging.getLogger()


def zip_if_directory(path):
    """If the path is a folder it zips it up and returns the new zipped path, otherwise returns existing
    file"""
    logger.info(f"Checking if path is directory: {path}")
    if os.path.isdir(path):
        base_path = os.path.dirname(os.path.dirname(path))  # gets parent directory
        folder_name = os.path.basename(path.strip("/"))
        logger.info(f"Zipping it up because it is directory, saving it to: {folder_name}.zip")
        new_path = shutil.make_archive(os.path.join(base_path, folder_name), 'zip', path)
        logger.info("New zip file path = " + new_path)
        return new_path
    else:
        return path


def get_data_key(obj, file_type, temp_directory, creator, index):
    file_name = obj.get(file_type)
    if not file_name:
        return

    file_path = os.path.join(temp_directory, file_name)
    if os.path.exists(file_path):
        new_dataset = Data(
            created_by=creator,
            type=file_type,
            name=f"{file_type} @ {timezone.now().strftime('%m-%d-%Y %H:%M')}",
            was_created_by_competition=True,
        )
        file_path = zip_if_directory(file_path)
        new_dataset.data_file.save(os.path.basename(file_path), File(open(file_path, 'rb')))
        return new_dataset.key
    elif len(file_name) in (32, 36):
        # UUID are 32 or 36 characters long
        if not Data.objects.filter(key=file_name).exists():
            raise CompetitionUnpackingException(f'Cannot find {file_type} with key: "{file_name}" for task: "{obj["name"]}"')
        return file_name
    else:
        raise CompetitionUnpackingException(f'Cannot find dataset: "{file_name}" for task: "{obj["name"]}"')


def get_datetime(field):
    if not field:
        return None
    elif isinstance(field, datetime.date):
        # turn the date into a datetime @ midnight that day
        field = datetime.datetime.combine(field, datetime.time())
    elif not isinstance(field, datetime.datetime):
        field = parser.parse(field)
    field = field.replace(tzinfo=timezone.now().tzinfo)
    return field
