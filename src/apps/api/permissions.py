from rest_framework import permissions


class IsOrganizerOrCollaborator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        is_collab = request.user in obj.collaborators.all() if hasattr(obj, 'collaborators') else False
        return request.user == obj.created_by or request.user.is_superuser or is_collab
