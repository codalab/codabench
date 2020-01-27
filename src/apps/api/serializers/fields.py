from rest_framework import serializers


class CharacterSeparatedField(serializers.CharField):
    """
    A field that separates a string with a given separator into
    a native list and reverts a list into a string separated with a given
    separator.
    """
    def __init__(self, *args, **kwargs):
        self.separator = kwargs.pop('separator', ',')
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        return value.split(self.separator)

    def to_internal_value(self, data):
        return self.separator.join([str(x) for x in data])
