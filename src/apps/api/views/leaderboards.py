from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from api.permissions import LeaderboardNotHidden, LeaderboardIsOrganizerOrCollaborator
from api.serializers.leaderboards import LeaderboardEntriesSerializer
from api.serializers.submissions import SubmissionScoreSerializer
from leaderboards.models import Leaderboard, SubmissionScore


class LeaderboardViewSet(ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardEntriesSerializer

    # TODO: The retrieve and list actions are the only ones used, apparently. Delete other permission checks soon!
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            raise Exception('Unexpected code branch execution.')
            self.permission_classes = [LeaderboardIsOrganizerOrCollaborator]
        elif self.action in ['create']:
            raise Exception('Unexpected code branch execution.')
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['retrieve', 'list']:
            self.permission_classes = [LeaderboardNotHidden]

        return [permission() for permission in self.permission_classes]

    def list(self, request, *args, **kwargs):
        # Return an empty list for the leaderboard-list endpoint
        return Response([])


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
