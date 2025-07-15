import os
from decimal import Decimal

from django.urls import reverse

from competitions.models import Submission
from factories import UserFactory
from tasks.models import Solution
from utils.storage import md5
from ..utils import SeleniumTestCase

LONG_WAIT = 4
SHORT_WAIT = 0.2


class TestSubmissions(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(password='test')

    def _run_submission_and_add_to_leaderboard(self, competition_zip_path, submission_zip_path, expected_submission_output, has_solutions=True, has_detailed_result=True, timeout=600, precision=2):
        """Creates a competition and runs a submission inside it, waiting for expected output to
        appear in submission realtime output panel.

        :param competition_zip_path: Relative to test_files/ dir
        :param submission_zip_path: Relative to test_files/ dir
        """
        self.login(username=self.user.username, password='test')

        self.get(reverse('competitions:upload'))
        self.find('input[ref="file_input"]').send_keys(os.path.join(self.test_files_dir, competition_zip_path))

        assert self.element_is_visible('div .ui.success.message')

        competition = self.user.competitions.first()
        comp_url = reverse("competitions:detail", kwargs={"pk": competition.id})
        submission_full_path = os.path.join(self.test_files_dir, submission_zip_path)
        self.find(f'a[href="{comp_url}"]').click()
        self.assert_current_url(comp_url)

        # This clicks the page before it loads fully, delay it a bit...
        self.wait(LONG_WAIT)
        self.find('.item[data-tab="participate-tab"]').click()

        self.circleci_screenshot("set_submission_file_name.png")
        self.find('input[ref="file_input"]').send_keys(submission_full_path)
        self.circleci_screenshot(name='uploading_submission.png')

        # The accordion shows "Running submission.zip"
        assert self.find_text_in_class('.submission-output-container .title', f"Running {submission_zip_path}", timeout=timeout)

        # Inside the accordion the output is being streamed
        self.wait(LONG_WAIT)
        self.find('.submission-output-container .title').click()
        self.wait(LONG_WAIT)
        assert self.find_text_in_class('.submission_output', expected_submission_output, timeout=timeout)

        # The submission table lists our submission!
        assert self.find('submission-manager#user-submission-table table tbody tr:nth-of-type(1) td:nth-of-type(2)').text == submission_zip_path

        # Check that md5 information was stored correctly
        submission_md5 = md5(f"./src/tests/functional{submission_full_path}")
        assert Submission.objects.filter(md5=submission_md5).exists()
        if has_solutions:
            assert Solution.objects.filter(md5=submission_md5).exists()

        # Get the submission ID for later comparison
        submission_id = int(self.find('submission-manager#user-submission-table table tbody tr:nth-of-type(1) td:nth-of-type(1)').text)

        # Add the submission to the leaderboard and go to results tab
        add_to_leaderboard_column = 7 if has_detailed_result else 6
        self.find(f'submission-manager#user-submission-table table tbody tr:nth-of-type(1) td:nth-of-type({add_to_leaderboard_column}) span[data-tooltip="Add to Leaderboard"]').click()
        self.find('.item[data-tab="results-tab"]').click()

        # The leaderboard table lists our submission
        prediction_score = Submission.objects.get(pk=submission_id).scores.first().score
        assert Decimal(self.find('leaderboards table tbody tr:nth-of-type(1) td:nth-of-type(5)').text) == round(Decimal(prediction_score), precision)

    def test_v15_iris_result_submission_end_to_end(self):
        self._run_submission_and_add_to_leaderboard('competition_15_iris.zip', 'submission_15_iris_result.zip', '======= Set 1 (Iris_test)', has_solutions=False, precision=4)

    def test_v15_iris_code_submission_end_to_end(self):
        self._run_submission_and_add_to_leaderboard('competition_15_iris.zip', 'submission_15_iris_code.zip', '======= Set 1 (Iris_test)', has_solutions=False, precision=4)

    def test_v18_submission_end_to_end(self):
        self._run_submission_and_add_to_leaderboard('competition_18.zip', 'submission_18.zip', 'results', has_solutions=False, has_detailed_result=False)

    def test_v2_submission_end_to_end(self):
        self._run_submission_and_add_to_leaderboard('competition.zip', 'submission.zip', 'Scores', has_detailed_result=False)
