import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework import permissions, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from django.urls import reverse

from api.permissions import IsUserAdminOrIsSelf, IsOrganizationEditor
from api.serializers.profiles import MyProfileSerializer, UserSerializer, OrganizationCreationSerializer, \
    OrganizationSerializer
from profiles.models import Organization, Membership

User = get_user_model()


class UserViewSet(mixins.UpdateModelMixin,
                  GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            self.permission_classes = [IsUserAdminOrIsSelf]
        return [permission() for permission in self.permission_classes]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        resp = self.get_serializer(instance)
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


class OrganizationViewSet(mixins.CreateModelMixin,
                          mixins.UpdateModelMixin,
                          GenericViewSet):

    def get_queryset(self):
        orgs = Organization.objects.all()
        if self.request.method in ['GET', 'LIST', 'CREATE']:
            return orgs
        elif self.request.method in ['PUT', 'PATCH']:
            return orgs.filter(users__in=[self.request.user])

    def get_serializer_class(self):
        if self.action == 'create':
            return OrganizationCreationSerializer
        else:
            return OrganizationSerializer

    def get_permissions(self):
        if self.action in ['create', 'retrieve', 'list']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOrganizationEditor]
        return [permission() for permission in self.permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = self.perform_create(serializer)

        # Set Creator to Owner
        obj.users.add(request.user)
        member = obj.membership_set.first()
        member.group = Membership.OWNER
        member.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()
