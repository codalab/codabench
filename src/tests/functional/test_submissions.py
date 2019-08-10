import uuid
from unittest import mock

from django.test import override_settings
from django.urls import reverse

from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory, PhaseFactory
from ..utils import SeleniumTestCase


class TestSubmissions(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(password='test')
        self.competition = CompetitionFactory(created_by=self.user, published=True)
        self.phase = PhaseFactory(competition=self.competition)
        # CompetitionParticipantFactory(user=self.user, competition=self.competition, status='approved')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    # @override_settings(DEBUG=True)
    def test_submission_appears_in_submissions_table(self):
        self.login(username=self.user.username, password='test')
        self.get(reverse('competitions:detail', kwargs={'pk': self.competition.id}))
        # with mock.patch('competitions.tasks.app.send_task') as celery_app:
        #     class Task:
        #         def __init__(self):
        #             self.id = uuid.uuid4()
        #     task = Task()
        #     celery_app.return_value = task
        #     self.circleci_screenshot("set_submission_file_name.png")
        #     self.find('input[ref="file_input"]').send_keys(f'{self.test_files_dir}/submission.zip')
        #     time = 0
        #     while time < 10 and not celery_app.called:
        #         self.wait(.5)
        #         time += .5
        #     assert celery_app.called
        #     assert celery_app.call_args[1]['queue'] == 'compute-worker'

        self.circleci_screenshot("set_submission_file_name.png")

        print(self.live_server_url)

        import time;time.sleep(1000)

        self.find('input[ref="file_input"]').send_keys(f'{self.test_files_dir}/submission.zip')

        assert self.element_is_visible('#output-modal')
        self.execute_script("$('#output-modal').modal('hide')")
        assert self.find('submission-manager table tbody tr:nth-of-type(1) td:nth-of-type(2)').text == 'submission.zip'
        submission = self.user.submission.first()
        created_files = [
            submission.data.data_file.name,
            submission.prediction_result.name,
            # TODO: Score the submission
            # submission.scoring_result.name,
        ]
        for detail in submission.details.all():
            created_files.append(detail.data_file.name)
        self.assert_storage_items_exist(*created_files)
        self.remove_items_from_storage(*created_files)
