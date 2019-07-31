from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.serializers.leaderboards import LeaderboardEntriesSerializer
from api.serializers.submissions import SubmissionScoreSerializer
from competitions.models import Submission
from leaderboards.models import Leaderboard, SubmissionScore


class LeaderboardViewSet(ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardEntriesSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.method == 'GET':
            qs = qs.prefetch_related(
                'submissions',
                'submissions__scores',
            )
        return qs


class SubmissionScoreViewSet(ModelViewSet):
    queryset = SubmissionScore.objects.all()
    serializer_class = SubmissionScoreSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        comp = instance.submissions.first().phase.competition
        admin_users = [comp.created_by] + list(comp.collaborators.all())
        if request.user not in admin_users and not request.user.is_superuser:
            raise PermissionError('You do not have permission to update submission scores')
        return super().update(request, *args, **kwargs)


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
