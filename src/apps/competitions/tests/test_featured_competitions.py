import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from competitions.models import Competition, CompetitionParticipant, Phase, Submission
from competitions.utils import get_featured_competitions, get_popular_competitions

User = get_user_model()


class FeaturedCompetitionsTests(TestCase):

    def setUp(self):
        '''
        1. Create two different users
        2. Create few competitions where published is True
        3. Add participants to competitions
        3. Return all competitions
        4. Return competitions with more participants
        '''

        self.user1 = User.objects.create(email="user1@test.com", username="user1", password="pass")
        self.user2 = User.objects.create(email="user2@test.com", username="user2", password="pass")
        self.user3 = User.objects.create(email="user3@test.com", username="user3", password="pass")
        self.user4 = User.objects.create(email="user4@test.com", username="user4", password="pass")

        self.competition1 = Competition.objects.create(title="competition1", created_by=self.user1, published=True)
        self.competition2 = Competition.objects.create(title="competition2", created_by=self.user1, published=True)
        self.competition3 = Competition.objects.create(title="competition3", created_by=self.user1, published=True)
        self.competition4 = Competition.objects.create(title="competition4", created_by=self.user1, published=True)
        self.competition5 = Competition.objects.create(title="competition5", created_by=self.user1, published=True)
        self.competition_old = Competition.objects.create(
            title="competition_old",
            created_by=self.user1,
            published=True,
            created_when=now() - datetime.timedelta(days=50)
        )

        self.participant1 = CompetitionParticipant.objects.create(user=self.user1, competition=self.competition1)
        self.participant2 = CompetitionParticipant.objects.create(user=self.user1, competition=self.competition2)
        self.participant3 = CompetitionParticipant.objects.create(user=self.user2, competition=self.competition2)
        self.participant4 = CompetitionParticipant.objects.create(user=self.user3, competition=self.competition1)
        self.participant5 = CompetitionParticipant.objects.create(user=self.user4, competition=self.competition1)
        self.participant6 = CompetitionParticipant.objects.create(user=self.user4, competition=self.competition2)
        self.participant7 = CompetitionParticipant.objects.create(user=self.user4, competition=self.competition4)
        self.participant8 = CompetitionParticipant.objects.create(user=self.user4, competition=self.competition3)
        self.participant9 = CompetitionParticipant.objects.create(user=self.user4, competition=self.competition4)
        self.participant10 = CompetitionParticipant.objects.create(user=self.user2, competition=self.competition3)
        self.participant12 = CompetitionParticipant.objects.create(user=self.user1, competition=self.competition5)

    # Comp 1 = 3
    # Comp 2 = 3
    # Comp 3 = 2
    # Comp 4 = 2

    def test_featured_comps(self):
        featured_list = get_featured_competitions()
        assert self.competition2 in featured_list

    def test_popular_comps(self):
        popular_list = get_popular_competitions()
        assert self.competition5 not in popular_list
