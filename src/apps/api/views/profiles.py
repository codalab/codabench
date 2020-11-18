import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.urls import reverse

from api.permissions import IsUserAdminOrIsSelf
from api.serializers.profiles import MyProfileSerializer, UserSerializer

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        return UserSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            self.permission_classes = [IsUserAdminOrIsSelf]
        return [permission() for permission in self.permission_classes]

    def get_serializer_class(self):
        return UserSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        resp = self.get_serializer(instance)
        print(resp.data['username'])
        return Response(reverse('profiles:user_profile', args=[resp.data['username']]))


class GetMyProfile(RetrieveAPIView, GenericAPIView):
    # queryset = User.objects.all()
    serializer_class = MyProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


@login_required
def user_lookup(request):
    search = request.GET.get('q', '')
    filters = Q()
    is_admin = request.user.is_superuser or request.user.is_staff

    if search:
        filters |= Q(username__icontains=search)
        filters |= Q(email__icontains=search) if is_admin else Q(email__iexact=search)

    users = User.objects.exclude(id=request.user.id).filter(filters)[:5]

    # Helper to print username with email for admins
    def _get_data(user):
        return {
            "id": user.id,
            "name": f"{user.name or user.username} ({user.email})" if is_admin else user.username,
            "username": user.username,
        }

    return HttpResponse(
        json.dumps({"results": [_get_data(u) for u in users]}),
    )
