from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.status import HTTP_405_METHOD_NOT_ALLOWED
from api.permissions import LeaderboardNotHidden
from api.serializers.leaderboards import LeaderboardEntriesSerializer
from api.serializers.submissions import SubmissionScoreSerializer
from leaderboards.models import Leaderboard, SubmissionScore


class LeaderboardViewSet(ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardEntriesSerializer
    http_method_names = ['get']  # Only allow GET requests

    def create(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed.'}, status=HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed.'}, status=HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed.'}, status=HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed.'}, status=HTTP_405_METHOD_NOT_ALLOWED)

    def list(self, request, *args, **kwargs):
        # Return an empty list for the leaderboard-list endpoint
        return Response([])

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return []  # No permissions, effectively disables the action
        elif self.action in ['retrieve', 'list']:
            self.permission_classes = [LeaderboardNotHidden]

        return [permission() for permission in self.permission_classes]


class SubmissionScoreViewSet(ModelViewSet):
    queryset = SubmissionScore.objects.all()
    serializer_class = SubmissionScoreSerializer

    def update(self, request, *args, **kwargs):
        instance = super().get_object()
        comp = instance.submissions.first().phase.competition
        if request.user not in comp.all_organizers and not request.user.is_superuser:
            raise PermissionError('You do not have permission to update submission scores')
        response = super().update(request, *args, **kwargs)
        for submission in instance.submissions.filter(parent__isnull=True):
            submission.calculate_scores()
        return response
