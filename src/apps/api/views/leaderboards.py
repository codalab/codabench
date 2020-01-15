from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.permissions import IsOrganizerOrCollaborator
from api.serializers.leaderboards import LeaderboardEntriesSerializer
from api.serializers.submissions import SubmissionScoreSerializer
from competitions.models import Submission
from leaderboards.models import Leaderboard, SubmissionScore


class LeaderboardViewSet(ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardEntriesSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOrganizerOrCollaborator]
        elif self.action in ['create']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['retrieve', 'list']:
            self.permission_classes = [AllowAny]
        return [permission() for permission in self.permission_classes]


class SubmissionScoreViewSet(ModelViewSet):
    queryset = SubmissionScore.objects.all()
    serializer_class = SubmissionScoreSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        comp = instance.submissions.first().phase.competition
        if request.user not in comp.all_organizers and not request.user.is_superuser:
            raise PermissionError('You do not have permission to update submission scores')
        response = super().update(request, *args, **kwargs)
        for submission in instance.submissions.filter(parent__isnull=True):
            submission.calculate_scores()
        return response


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def add_submission_to_leaderboard(request, submission_pk):
    # TODO: rebuild this to look somewhere else for what leaderboard to post to?
    submission = get_object_or_404(Submission, pk=submission_pk)

    # Removing any existing submissions on leaderboard
    submission.phase.submissions.filter(owner=request.user).exclude(leaderboard=None).update(leaderboard=None)

    # toggle submission on or off, if it was already on leaderboard
    if not submission.leaderboard:
        print(f"Adding {submission} to {submission.leaderboard}")
        submission.leaderboard = submission.phase.competition.leaderboards.all()[0]
    else:
        print(f"Removing {submission} from {submission.leaderboard}")
        submission.leaderboard = None

    submission.save()

    return Response({})
