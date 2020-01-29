from rest_framework.relations import SlugRelatedField


class SlugWriteDictReadField(SlugRelatedField):

    def __init__(self, read_serializer, **kwargs):
        self.read_serializer = read_serializer
        super().__init__(**kwargs)

    def to_representation(self, obj):
        return self.read_serializer(obj).data
