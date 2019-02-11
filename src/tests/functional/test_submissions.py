from django.urls import reverse

from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory, PhaseFactory
from ..utils import SeleniumTestCase


class TestSubmissions(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(password='test')
        self.competition = CompetitionFactory(created_by=self.user, published=True)
        self.phase = PhaseFactory(competition=self.competition)
        CompetitionParticipantFactory(user=self.user, competition=self.compettition, status='approved')

    def test_submission_appears_in_submissions_table(self):
        self.login(username=self.user.username, password='test')
        self.get(reverse('competitions:detail', kwargs={'pk': self.competition.id}))

        # Before clicking this button, mock app.send_task SO IT ISN'T ACTUALLY CALLED!
        # with mock.patch('competitions.tasks.app.send_task') as celery_app:
        #     celery_app.returns = {"id": 1}
        #
        #     self.find('input[ref="file_input"]').send_keys(f'{self.test_files_dir}/submission.zip')
        #
        #     assert celery_app.called
        #     assert 'queue' in celery_app.last_called_arguments
        #     assert celery_app.last_called_arguments['queue'] == 'compute-worker'

        # assert self.find('#output-modal')  # make sure our modal has popped up

        self.execute_script("$('#output-modal').modal('hide')")



        # sub = Submission.objects.get(pk=submission_pk_somehow)
        # assert BundleStorage.exists(sub.data.data_file)


        assert self.find('submission-manager table tbody tr:nth-of-type(1) td:nth-of-type(2)').text == 'submission.zip'
