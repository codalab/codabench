import logging

from django.db.models import Sum, Q
from rest_framework.generics import get_object_or_404

from competitions.models import Submission
from leaderboards.models import Leaderboard

logger = logging.getLogger(__name__)


class BaseModeStrategy:

    def get_submission_and_phase_and_leaderboard(self, submission_pk):
        submission = get_object_or_404(Submission, pk=submission_pk)
        phase = submission.phase
        leaderboard = phase.leaderboard
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
        self.do_execute(phase, request, submission)

        self.update_submission(submission=submission,
                               submission_pk=submission_pk,
                               leaderboard=leaderboard)

    def do_execute(self, phase, request, submission):
        pass


class ManualModeStrategy(BaseModeStrategy):

    def put_on_leaderboard(self, request, submission_pk):
        """do nothing by default"""
        pass

    def __str__(self):
        return "ManuallyModeStrategy"


class LastestModeStrategy(BaseModeStrategy):

    def do_execute(self, phase, request, submission):
        """add latest submission in leaderboard"""
        Submission.objects.filter(phase=phase, owner=submission.owner).update(leaderboard=None)

    def __str__(self):
        return "LastestModeStrategy"


class AllModeStrategy(BaseModeStrategy):

    def __str__(self):
        return "AllModeStrategy"


class BestModeStrategy(BaseModeStrategy):

    def put_on_leaderboard(self, request, submission_pk):
        """fetch all submission, then choose best submission and put on leaderboard"""
        submission, phase, leaderboard = super().get_submission_and_phase_and_leaderboard(submission_pk=submission_pk)

        Submission.objects.filter(phase=phase, owner=submission.owner).update(leaderboard=None)
        best_submission = self._choose_best_submission(leaderboard=leaderboard, owner=submission.owner, phase=phase)

        super().update_submission(submission=best_submission,
                                  submission_pk=best_submission.id,
                                  leaderboard=leaderboard)

    def _choose_best_submission(self, leaderboard, owner, phase):
        """choose best submission"""
        primary_col = leaderboard.columns.get(index=leaderboard.primary_index)
        ordering = [f'{"-" if primary_col.sorting == "desc" else ""}primary_col']

        submissions = Submission.objects.filter(phase=phase,
                                                owner=owner,
                                                is_soft_deleted=False,
                                                status=Submission.FINISHED) \
            .select_related('owner').prefetch_related('scores') \
            .annotate(primary_col=Sum('scores__score', filter=Q(scores__column=primary_col)))

        for column in leaderboard.columns.exclude(id=primary_col.id).order_by('index'):
            col_name = f'col{column.index}'
            ordering.append(f'{"-" if column.sorting == "desc" else ""}{col_name}')
            kwargs = {
                col_name: Sum('scores__score', filter=Q(scores__column__index=column.index))
            }
            submissions = submissions.annotate(**kwargs)

        submissions = submissions.order_by(*ordering, 'created_when')
        return submissions[0]

    def __str__(self):
        return "BestModeStrategy"


class StrategyFactory:

    @staticmethod
    def create_by_submission_rule(submission_rule):
        if Leaderboard.FORCE_LAST == submission_rule:
            return LastestModeStrategy()
        elif Leaderboard.FORCE_LATEST_MULTIPLE == submission_rule:
            return AllModeStrategy()
        elif Leaderboard.FORCE_BEST == submission_rule:
            return BestModeStrategy()
        else:
            return ManualModeStrategy()


def put_on_leaderboard_by_submission_rule(request, submission_pk, submission_rule):
    """add submission score to leaderboard by display strategy"""
    strategy = StrategyFactory.create_by_submission_rule(submission_rule)
    strategy.put_on_leaderboard(request, submission_pk)
