import os
import uuid


def get_path_wrapper(directory):
    """
    Creates a helper function that takes the given object and returns a folder name appended
    with a portion of a UUID. UUID is included not to prevent collisions, but to prevent
    potential scraping of data.

    :param directory: The directory name to put the file
    :return: A wrapped function taking an object and filename, that returns a unique path
    """
    """Helper to generate UUID's in file names while maintaining their extension"""
    def wrapped_uuidify(obj, filename):
        name, extension = os.path.splitext(filename)
        truncated_uuid = str(uuid.uuid4())[0:5]
        truncated_name = name[0:35]
        return os.path.join(directory, str(obj.pk), truncated_uuid, "{0}{1}".format(truncated_name, extension))
    return wrapped_uuidify
