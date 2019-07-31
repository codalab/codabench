from django.urls import reverse
from rest_framework.test import APITestCase

from competitions.models import CompetitionParticipant
from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory


class CompetitionParticipantTests(APITestCase):
    def setUp(self):
        self.admin = UserFactory(username='admin', password='admin', super_user=True)
        self.user = UserFactory(username='creator', password='creator')
        self.norm = UserFactory(username='norm', password='norm')
        self.collab = UserFactory(username='collab', password='collab')
        self.comp = CompetitionFactory(created_by=self.user, collaborators=[self.collab], published=True)
        for _ in range(5):
            CompetitionParticipantFactory(competition=self.comp)

    def get_participants(self, competition=None):
        competition = competition if competition is not None else self.comp
        return self.client.get(reverse('participants-list') + f'?competition={competition.id}')

    def test_login_required_to_see_participants(self):
        resp = self.get_participants()
        assert resp.status_code == 403

    def test_superuser_can_see_participants(self):
        self.client.login(username='admin', password='admin')
        resp = self.get_participants()
        assert resp.status_code == 200
        assert len(resp.json()) == CompetitionParticipant.objects.filter(competition=self.comp).count()

    def test_comp_creator_can_see_participants(self):
        self.client.login(username='creator', password='creator')
        resp = self.get_participants()
        assert resp.status_code == 200
        assert len(resp.json()) == CompetitionParticipant.objects.filter(competition=self.comp).count()

    def test_collab_can_see_participants(self):
        self.client.login(username='collab', password='collab')
        resp = self.get_participants()
        assert resp.status_code == 200
        assert len(resp.json()) == CompetitionParticipant.objects.filter(competition=self.comp).count()

    def test_normal_user_cannot_see_participants(self):
        self.client.login(username='norm', password='norm')
        resp = self.get_participants()
        assert CompetitionParticipant.objects.filter(competition=self.comp).count() > 0
        assert len(resp.json()) == 0
