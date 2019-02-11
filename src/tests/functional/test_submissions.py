from django.urls import reverse

from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory, PhaseFactory
from ..utils import SeleniumTestCase


class TestSubmissions(SeleniumTestCase):
    def test_submission_appears_in_submissions_table(self):
        user = UserFactory(password='test')
        self.login(username=user.username, password='test')
        comp = CompetitionFactory(created_by=user, published=True)
        phase = PhaseFactory(competition=comp)
        CompetitionParticipantFactory(user=user, competition=comp, status='approved')
        self.get(reverse('competitions:detail', kwargs={'pk': comp.id}))
        # import ipdb; ipdb.set_trace()
        self.find('input[ref="file_input"]').send_keys(f'{self.test_files_dir}/submission.zip')
        self.execute_script("$('#output-modal').modal('hide')")
        assert self.find('submission-manager table tbody tr:nth-of-type(1) td:nth-of-type(2)').text == 'submission.zip'
