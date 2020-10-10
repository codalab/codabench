from django.db.models import Sum, Q
from rest_framework.generics import get_object_or_404

from competitions.models import Submission

MANUALLY = 'manually'
LATSET = 'latest'
ALL = 'all'
BEST = 'best'


class BaseModeHandler:

    def get_submission_and_phase_and_leaderboard(self, submission_pk):
        submission = get_object_or_404(Submission, pk=submission_pk)
        phase = submission.phase
        leaderboard = submission.phase.leaderboard

        return submission, phase, leaderboard

    def update_submission(self, submission, submission_pk, leaderboard):
        if submission.has_children:
            for s in Submission.objects.filter(parent=submission_pk):
                s.leaderboard = leaderboard
                s.save()
        else:
            submission.leaderboard = leaderboard
            submission.save()

    def put_on_leaderboard(self, request, submission_pk):
        submission, phase, leaderboard = self.get_submission_and_phase_and_leaderboard(submission_pk=submission_pk)

        # process specify logic for different mode(for difference display mode)
        self.do_execute(phase, request)

        self.update_submission(submission=submission,
                               submission_pk=submission_pk,
                               leaderboard=leaderboard)

    def do_execute(self, phase, request):
        pass


class ManuallyModeHanlder(BaseModeHandler):

    def put_on_leaderboard(self, request, submission_pk):
        """do nothing by default"""
        pass


class LastestModeHandler(BaseModeHandler):

    def do_execute(self,phase, request):
        """add latest submission in leaderboard"""

        # Removing any existing submissions on leaderboard
        Submission.objects.filter(phase=phase, owner=request.user).update(leaderboard=None)


class AllModeHandler(BaseModeHandler):
    pass


class BestModeHandler(BaseModeHandler):

    def put_on_leaderboard(self, request, submission_pk):
        """fetch all submission, then choose best submission and put on leaderboard"""
        submission, phase, leaderboard = super().get_submission_and_phase_and_leaderboard(submission_pk=submission_pk)

        best_submission = self._choose_best_submission(leaderboard=leaderboard, request=request, phase=phase)

        super().update_submission(submission=best_submission,
                                  submission_pk=best_submission.id,
                                  leaderboard=leaderboard)

    def _choose_best_submission(self, leaderboard, request, phase):
        """choose best submission"""
        primary_col = leaderboard.columns.get(index=leaderboard.primary_index)
        # Order first by primary column. Then order by other columns after for tie breakers.
        ordering = [f'{"-" if primary_col.sorting == "desc" else ""}primary_col']
        submissions = Submission.objects.filter(phase=phase, owner=request.user)

        for column in leaderboard.columns.exclude(id=primary_col.id).order_by('index'):
            col_name = f'col{column.index}'
            ordering.append(f'{"-" if column.sorting == "desc" else ""}{col_name}')
            kwargs = {
                col_name: Sum('scores__score', filter=Q(scores__column__index=column.index))
            }
            submissions = submissions.annotate(**kwargs)

        submissions = submissions.order_by(*ordering, 'created_when')
        return submissions[0]


class HandlerFactory:

    @staticmethod
    def create_by_mode(display_mode):
        """get leaderboard display mode handler by display mode config in competiton model"""
        if MANUALLY == display_mode:
            return ManuallyModeHanlder()
        elif LATSET == display_mode:
            return LastestModeHandler()
        elif AllModeHandler == display_mode:
            return AllModeHandler()
        elif BEST == BestModeHandler:
            return BestModeHandler()
