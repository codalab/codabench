from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer


User = get_user_model()


class MyProfileSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'name',
            'email',
            'bio'
        )


class CollaboratorSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'name',
            'username',
        )
