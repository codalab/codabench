from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny

from api.pagination import LargePagination
from api.serializers.external_competitions import ExternalCompetitionSerializer, ExternalPlatformFilterSerializer
from external_competitions.models import ExternalCompetition, ExternalPlatform


class ExternalCompetitionListView(generics.ListAPIView):
    serializer_class = ExternalCompetitionSerializer
    permission_classes = (AllowAny,)
    pagination_class = LargePagination
    filter_backends = (SearchFilter,)
    search_fields = ('name', 'description', 'organizer_name')

    def get_queryset(self):
        # NOTE
        # platform.is_active only controls whether the fetch task pulls from that
        # platform - it doesn't hide already-fetched competitions from the public list.
        # If in the future you don't want to show competitions from non active platfroms,
        # Add a filter to the query below: `.filter(platform__is_active=True)`
        queryset = ExternalCompetition.objects.select_related('platform')

        # Comma-separated list of platform ids, e.g. ?platform=1,2
        platform_ids = self.request.query_params.get('platform')
        if platform_ids:
            queryset = queryset.filter(platform_id__in=platform_ids.split(','))

        return queryset


class ExternalPlatformListView(generics.ListAPIView):
    serializer_class = ExternalPlatformFilterSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        # NOTE
        # Not filtering by is_active: a deactivated platform's competitions still show
        # in the list above, so it must stay selectable as a filter option here too.
        # If in the future you don't want to show non active platfroms, 
        # Add a filter to the query below: `.filter(is_active=True)`
        return ExternalPlatform.objects.order_by('name')
