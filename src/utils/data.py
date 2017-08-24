import os
import uuid

from django.utils.deconstruct import deconstructible


@deconstructible
class PathWrapper(object):
    """Helper to generate UUID's in file names while maintaining their extension"""

    def __init__(self, base_directory):
        self.path = base_directory

    def __call__(self, instance, filename):
        name, extension = os.path.splitext(filename)
        truncated_uuid = str(uuid.uuid4())[0:5]
        truncated_name = name[0:35]
        return os.path.join(
            self.path,
            str(instance.pk),
            truncated_uuid,
            "{0}{1}".format(truncated_name, extension)
        )
