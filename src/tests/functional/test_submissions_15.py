import os

from django.urls import reverse

from factories import UserFactory
from ..utils import SeleniumTestCase


class TestSubmissions(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(password='test')

    def test_submission_appears_in_submissions_table(self):
        self.login(username=self.user.username, password='test')

        self.get(reverse('competitions:upload'))
        self.find('input[ref="file_input"]').send_keys(os.path.join(self.test_files_dir, 'competition_15.zip'))

        assert self.element_is_visible('div .ui.success.message')

        competition = self.user.competitions.first()
        comp_url = reverse("competitions:detail", kwargs={"pk": competition.id})
        self.find(f'a[href="{comp_url}"]').click()
        self.assert_current_url(comp_url)

        # This clicks the page before it loads fully, delay it a bit...
        self.wait(1)
        self.find('.item[data-tab="participate-tab"]').click()

        self.circleci_screenshot("set_submission_file_name.png")
        self.find('input[ref="file_input"]').send_keys(os.path.join(self.test_files_dir, 'submission_15.zip'))
        self.circleci_screenshot(name='uploading_submission.png')

        # The accordion shows "Running submission.zip"
        assert self.find_text_in_class('.submission-output-container .title', "Running submission_15.zip", timeout=650)

        # Inside the accordion the output is being streamed
        self.find('.submission-output-container .title').click()
        # assert self.find_text_in_class('.submission_output', 'Scores')
        # assert self.find_text_in_class('.submission_output', 'accuracy')

        # The submission table lists our submission!
        assert self.find('submission-manager table tbody tr:nth-of-type(1) td:nth-of-type(2)').text == 'submission_15.zip'

        submission = self.user.submission.first()
        task = competition.phases.first().tasks.first()
        created_files = [
            # Competition related files
            competition.bundle_dataset.data_file.name,
            competition.logo.name,
            task.scoring_program.data_file.name,
            task.reference_data.data_file.name,

            # Submission related files
            submission.data.data_file.name,
            submission.prediction_result.name,
            submission.scoring_result.name,
        ]
        for detail in submission.details.all():
            created_files.append(detail.data_file.name)

        self.assert_storage_items_exist(*created_files)
        self.remove_items_from_storage(*created_files)
