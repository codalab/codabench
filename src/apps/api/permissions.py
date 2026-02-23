from django.conf import settings
from django.contrib.auth.models import Group
from rest_framework import permissions

from profiles.models import Membership


def _get_competition_creator_group_name():
    return getattr(settings, "COMPETITION_CREATOR_GROUP", "").strip()


def is_creator_group_missing():
    group_name = _get_competition_creator_group_name()

    return bool(group_name) and (not Group.objects.filter(name=group_name).exists())


def user_can_create_competition(user):
    if not user or not user.is_authenticated:
        return False

    group_name = _get_competition_creator_group_name()
    if not group_name:
        return True

    # if configured group is missing, deny creation.
    if not Group.objects.filter(name=group_name).exists():
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=group_name).exists()


class IsCompetitionCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        if is_creator_group_missing():
            self.message = (
                "Competition creation is disabled: configured COMPETITION_CREATOR_GROUP does not exist."
            )
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
