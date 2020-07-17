import os
from decimal import Decimal

from django.urls import reverse

from competitions.models import Submission
from factories import UserFactory
from tasks.models import Solution
from utils.storage import md5
from ..utils import SeleniumTestCase


class TestSubmissions(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(password='test')

    def _run_submission_and_add_to_leaderboard(self, competition_zip_path, submission_zip_path, expected_submission_output, has_solutions=True, timeout=999):
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
        self.wait(1)
        self.find('.item[data-tab="participate-tab"]').click()

        self.circleci_screenshot("set_submission_file_name.png")
        self.find('input[ref="file_input"]').send_keys(submission_full_path)
        self.circleci_screenshot(name='uploading_submission.png')

        # The accordion shows "Running submission.zip"
        assert self.find_text_in_class('.submission-output-container .title', f"Running {submission_zip_path}", timeout=timeout)

        # Inside the accordion the output is being streamed
        self.find('.submission-output-container .title').click()
        self.wait(1)
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
        self.find('submission-manager#user-submission-table table tbody tr:nth-of-type(1) td:nth-of-type(4)').click()
        self.find('.item[data-tab="results-tab"]').click()

        self.wait(1)

        # The leaderboard table lists our submission
        prediction_score = Submission.objects.get(pk=submission_id).scores.first().score
        print('prediction score: ', prediction_score)
        print('on page: ', Decimal(self.find('leaderboards table tbody tr:nth-of-type(1) td:nth-of-type(3)').text))
        assert Decimal(self.find('leaderboards table tbody tr:nth-of-type(1) td:nth-of-type(3)').text) == prediction_score

    def test_v15_submission_end_to_end(self):
        self._run_submission_and_add_to_leaderboard('competition_15.zip', 'submission_15.zip', '*** prediction_score', has_solutions=False)

    def test_v2_submission_end_to_end(self):
        self._run_submission_and_add_to_leaderboard('competition.zip', 'submission.zip', 'Scores')
