import base64

import binascii
import json
# import uuid

import six
from django.core.files.base import ContentFile
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework.relations import SlugRelatedField


class NamedBase64ImageField(Base64ImageField):

    def to_internal_value(self, named_json_data):
        # Check if this is a base64 string
        if named_json_data in self.EMPTY_VALUES:
            return None

        data = json.loads(named_json_data)
        file_name = data["file_name"]
        base64_data = data["data"]

        if isinstance(base64_data, six.string_types):
            # Strip base64 header.
            if ';base64,' in base64_data:
                header, base64_data = base64_data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(base64_data)
            except (TypeError, binascii.Error):
                raise ValidationError(self.INVALID_FILE_MESSAGE)

            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)
            if file_extension not in self.ALLOWED_TYPES:
                raise ValidationError(self.INVALID_TYPE_MESSAGE)

            data = ContentFile(decoded_file, name=file_name)
            return data
        raise ValidationError(('This is not an base64 string'))


class SlugWriteDictReadField(SlugRelatedField):

    def __init__(self, read_serializer, **kwargs):
        self.read_serializer = read_serializer
        super().__init__(**kwargs)

    def to_representation(self, obj):
        return self.read_serializer(obj).data
