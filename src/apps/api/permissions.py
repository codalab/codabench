from django.conf import settings
from rest_framework import permissions

from profiles.models import Membership


def competition_creation_enabled_by_default():
    return getattr(settings, "COMPETITION_CREATION_ENABLED_BY_DEFAULT", True)


def user_can_create_competition(user):
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    user_override = getattr(user, "can_create_competition", None)
    if user_override is not None:
        return user_override

    return competition_creation_enabled_by_default()


class IsCompetitionCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        return user_can_create_competition(request.user)


class IsOrganizerOrCollaborator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        is_collab = request.user in obj.collaborators.all() if hasattr(obj, 'collaborators') else False
        return request.user == obj.created_by or request.user.is_superuser or is_collab


class LeaderboardIsOrganizerOrCollaborator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        obj = obj.phases.first().competition
        is_collab = request.user in obj.collaborators.all() if hasattr(obj, 'collaborators') else False
        return request.user == obj.created_by or request.user.is_superuser or is_collab


class LeaderboardNotHidden(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.phases.first().competition.user_has_admin_permission(request.user):
            return True
        else:
            return not obj.hidden


class IsUserAdminOrIsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or request.user == obj


class IsOrganizationEditor(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        try:
            membership = obj.membership_set.get(user=request.user)
        except Membership.DoesNotExist:
            return False
        return membership.group in membership.EDITORS_GROUP
