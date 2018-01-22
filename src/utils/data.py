import os
import uuid

import time
from django.utils.deconstruct import deconstructible


@deconstructible
class PathWrapper(object):
    """Helper to generate UUID's in file names while maintaining their extension"""

    def __init__(self, base_directory):
        self.path = base_directory

    def __call__(self, instance, filename):
        name, extension = os.path.splitext(filename)
        truncated_uuid = uuid.uuid4().hex[0:12]
        truncated_name = name[0:35]
        return os.path.join(
            self.path,
            time.strftime('%Y/%m/%d'),
            truncated_uuid,
            "{0}{1}".format(truncated_name, extension)
        )
