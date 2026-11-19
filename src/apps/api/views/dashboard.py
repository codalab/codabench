from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny

from api.serializers.competitions import DashboardCompetitionSerializer
from competitions.models import Competition


class DashboardCompetitionsView(generics.ListAPIView):
    """
    Returns only the fields strictly needed by dashboard charts and tables.
    """
    permission_classes = (AllowAny,)
    serializer_class = DashboardCompetitionSerializer
    pagination_class = None  # Disable pagination for this endpoint

    def get_queryset(self):
        visibility = self.request.query_params.get('visibility', 'public')

        if visibility not in ('public', 'private', 'all'):
            raise ValidationError("Invalid visibility parameter. Must be one of 'public', 'private', or 'all'.")

        user_is_admin = self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)

        # Restrict private and all visibility to staff and superusers
        if visibility in ('private', 'all'):
            if not user_is_admin:
                raise PermissionDenied("You cannot view private competitions if you are not a superuser or staff member.")

        qs = Competition.objects.all().select_related('created_by').prefetch_related('tags__category')

        if visibility == 'public':
            qs = qs.filter(published=True)
        elif visibility == 'private':
            qs = qs.filter(published=False)
        # else 'all': no published filter applied

        competition_type = self.request.query_params.get('type', 'any')
        if competition_type != 'any':
            qs = qs.filter(competition_type=competition_type)

        qs = qs.only(
            'id',
            'title',
            'created_when',
            'published',
            'participants_count',
            'submissions_count',
            'competition_type',
            'reward',
            'created_by__id',
            'created_by__username',
            'created_by__display_name',
        )
        return qs
