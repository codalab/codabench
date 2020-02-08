class DefaultUserCreateMixin:
    """This will automatically set `YourModel.user` to `request.user`. To override which
    attribute the user is written to, add a `user_field` to your classes Meta information

    Example:
        class MySerializer(DefaultUserCreateMixin, ModelSerializer):
            class Meta:
                model = YourModel
                # YourModel.owner = a foreign key to request.user
                user_field = 'owner'
    """
    def create(self, validated_data):
        user_field = getattr(self.Meta, 'user_field', 'user')
        if user_field not in validated_data:
            if 'request' not in self.context:
                raise Exception('self.context does not contain "request". Have you overwritten get_serializer_context?')
            validated_data[user_field] = self.context['request'].user
        return super().create(validated_data)
