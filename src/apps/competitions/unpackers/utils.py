import datetime
import os
import shutil

from dateutil import parser
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)


class CompetitionUnpackingException(Exception):
    pass


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


def get_datetime(field):
    if not field:
        return None
    elif isinstance(field, datetime.date):
        # turn the date into a datetime @ midnight that day
        field = datetime.datetime.combine(field, datetime.time())
    elif not isinstance(field, datetime.datetime):
        field = parser.parse(field)
    return field.replace(tzinfo=timezone.now().tzinfo)
