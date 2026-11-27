import logging

from django.db.models import F, Avg, Q
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

    def put_on_leaderboard(self, request, submission_pk):
        """
        Put the latest submission on the leaderboard.
        For a multi-task submission, wait until every task has sent its scores.
        Why: each task sends its scores separately. Replacing the row earlier removes
        the other tasks and shows n/a for them.
        """
        submission, phase, leaderboard = self.get_submission_and_phase_and_leaderboard(submission_pk=submission_pk)

        if submission.parent is None:
            super().put_on_leaderboard(request=request, submission_pk=submission_pk)
            return

        children = Submission.objects.filter(parent=submission.parent)
        if children.filter(scores__isnull=True).exists():
            return

        self.do_execute(phase=phase, request=request, submission=submission)
        children.update(leaderboard=leaderboard)

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

        # A child of a multi-task submission is not ranked on its own: wait until its parent is a candidate, so the
        # current best stays on the leaderboard while the other tasks are still running
        if submission.parent_id is not None and submission.parent_id not in self._candidate_pks(submission):
            return

        Submission.objects.filter(phase=phase, owner=submission.owner).update(leaderboard=None)
        best_submission = self._choose_best_submission(leaderboard=leaderboard, owner=submission.owner, phase=phase,
                                                       scored_submission=submission)

        super().update_submission(submission=best_submission,
                                  submission_pk=best_submission.id,
                                  leaderboard=leaderboard)

    def _choose_best_submission(self, leaderboard, owner, phase, scored_submission):
        """choose best submission"""
        primary_col = leaderboard.columns.get(index=leaderboard.primary_index)
        ordering = [self._null_last_order(name='primary_col', sorting=primary_col.sorting)]

        # Only top-level submissions are ranked. A multi-task parent holds the score rows of all its children, so
        # Avg ranks it on its mean across tasks; ranking its children too would let one task beat the whole submission.
        # Avg also gives a single-row score unchanged, and the real score for old duplicate rows instead of a multiple.
        submissions = Submission.objects.filter(phase=phase,
                                                owner=owner,
                                                parent__isnull=True,
                                                is_soft_deleted=False) \
            .filter(Q(status=Submission.FINISHED) | Q(pk__in=self._candidate_pks(scored_submission))) \
            .select_related('owner').prefetch_related('scores') \
            .annotate(primary_col=Avg('scores__score', filter=Q(scores__column=primary_col)))

        for column in leaderboard.columns.exclude(id=primary_col.id).order_by('index'):
            col_name = f'col{column.index}'
            ordering.append(self._null_last_order(name=col_name, sorting=column.sorting))
            kwargs = {
                col_name: Avg('scores__score', filter=Q(scores__column__index=column.index))
            }
            submissions = submissions.annotate(**kwargs)

        # On equal scores the oldest submission wins, so a new submission only replaces the current best if it scores better
        submissions = submissions.order_by(*ordering, 'created_when')
        return submissions[0]

    def _candidate_pks(self, scored_submission):
        """pks of the submissions that are candidates even though they are not Finished yet

        The compute worker only marks a submission Finished after its scores are uploaded, so the submission whose
        scores are being uploaded is a candidate before it is Finished. Its parent is too once every other child is
        done: Finished, Failed or Cancelled, or with its scores already uploaded (a sibling that finished at about the
        same time may not be marked Finished yet). Sibling uploads are serialized by a lock on the parent row in
        upload_submission_scores, so each one sees the scores of the ones before it.
        """
        pks = [scored_submission.pk]
        parent = scored_submission.parent
        if parent is not None:
            done_statuses = [Submission.FINISHED, Submission.FAILED, Submission.CANCELLED]
            pending_siblings = parent.children.exclude(pk=scored_submission.pk) \
                .exclude(status__in=done_statuses) \
                .filter(scores__isnull=True)
            if not pending_siblings.exists():
                pks.append(parent.pk)
        return pks

    def _null_last_order(self, name, sorting):
        """order by an annotated column, keeping submissions without a score at the end"""
        return F(name).desc(nulls_last=True) if sorting == "desc" else F(name).asc(nulls_last=True)

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
