from django.contrib.auth import get_user_model
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework import permissions

from api.serializers.profiles import MyProfileSerializer

User = get_user_model()


class GetMyProfile(RetrieveAPIView, GenericAPIView):
    # queryset = User.objects.all()
    serializer_class = MyProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
