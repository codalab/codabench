from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from api.permissions import LeaderboardNotHidden, LeaderboardIsOrganizerOrCollaborator
from api.serializers.leaderboards import LeaderboardEntriesSerializer
from api.serializers.submissions import SubmissionScoreSerializer
from competitions.models import Submission
from leaderboards.models import Leaderboard, SubmissionScore
import rest_framework.exceptions as drf_exceptions


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


def is_user_submission_owner_or_admin(request, submission, competition):
    if request.user.is_superuser or request.user in competition.collaborators.all():
        return True
    elif request.user == submission.owner:
        return True
    else:
        raise drf_exceptions.AuthenticationFailed("You do not have permission to change this submission's leaderboard status")


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def add_submission_to_leaderboard(request, submission_pk):
    submission = get_object_or_404(Submission, pk=submission_pk)
    phase = submission.phase
    is_user_submission_owner_or_admin(request, submission, phase.competition)

    # Removing any existing submissions on leaderboard
    Submission.objects.filter(phase=phase, owner=submission.owner).update(leaderboard=None)

    leaderboard = submission.phase.leaderboard

    if submission.has_children:
        for s in Submission.objects.filter(parent=submission_pk):
            s.leaderboard = leaderboard
            s.save()
    else:
        submission.leaderboard = leaderboard
        submission.save()

    return Response({})


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def remove_submission_from_leaderboard(request, submission_pk):
    submission = get_object_or_404(Submission, pk=submission_pk)
    competition = submission.phase.competition
    is_user_submission_owner_or_admin(request, submission, competition)
    if submission.leaderboard.submission_rule != "Add_And_Delete":
        raise drf_exceptions.ValidationError("You are not allowed to remove a submission on this phase")
    submission.leaderboard = None
    submission.save()

    return Response({})
