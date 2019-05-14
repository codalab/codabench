from django.test import TestCase
from django.contrib.auth import get_user_model

from competitions.models import Competition, CompetitionParticipant
from competitions.utils import get_featured_competitions, get_popular_competitions

User = get_user_model()


class FeaturedCompetitionsTests(TestCase):

    def setUp(self):
        """
        1. Create two different users
        2. Create few competitions where published is True
        3. Add participants to competitions
        3. Return all competitions
        4. Return competitions with more participants
        """

        self.user1 = User.objects.create(email="user1@test.com", username="user1", password="pass")
        self.user2 = User.objects.create(email="user2@test.com", username="user2", password="pass")
        self.user3 = User.objects.create(email="user3@test.com", username="user3", password="pass")
        self.user4 = User.objects.create(email="user4@test.com", username="user4", password="pass")
        self.user5 = User.objects.create(email="user5@test.com", username="user5", password="pass")
        self.user6 = User.objects.create(email="user6@test.com", username="user6", password="pass")
        self.user7 = User.objects.create(email="user7@test.com", username="user7", password="pass")

        self.competition1 = Competition.objects.create(title="competition1", created_by=self.user1, published=True)
        self.competition2 = Competition.objects.create(title="competition2", created_by=self.user1, published=True)
        self.competition3 = Competition.objects.create(title="competition3", created_by=self.user1, published=True)
        self.competition4 = Competition.objects.create(title="competition4", created_by=self.user1, published=True)
        self.competition5 = Competition.objects.create(title="competition5", created_by=self.user1, published=True)
        self.competition6 = Competition.objects.create(title="competition6", created_by=self.user1, published=True)
        self.competition7 = Competition.objects.create(title="competition7", created_by=self.user1, published=True)

        # Competition One Participants
        CompetitionParticipant.objects.create(user=self.user1, competition=self.competition1)
        CompetitionParticipant.objects.create(user=self.user2, competition=self.competition1)
        CompetitionParticipant.objects.create(user=self.user3, competition=self.competition1)
        CompetitionParticipant.objects.create(user=self.user4, competition=self.competition1)
        CompetitionParticipant.objects.create(user=self.user5, competition=self.competition1)
        CompetitionParticipant.objects.create(user=self.user6, competition=self.competition1)
        CompetitionParticipant.objects.create(user=self.user7, competition=self.competition1)

        # Competition Two Participants
        CompetitionParticipant.objects.create(user=self.user1, competition=self.competition2)
        CompetitionParticipant.objects.create(user=self.user2, competition=self.competition2)
        CompetitionParticipant.objects.create(user=self.user3, competition=self.competition2)
        CompetitionParticipant.objects.create(user=self.user4, competition=self.competition2)
        CompetitionParticipant.objects.create(user=self.user5, competition=self.competition2)

        # Competition Three Participants
        CompetitionParticipant.objects.create(user=self.user4, competition=self.competition3)
        CompetitionParticipant.objects.create(user=self.user2, competition=self.competition3)
        CompetitionParticipant.objects.create(user=self.user3, competition=self.competition3)

        # Competition Four Participants
        CompetitionParticipant.objects.create(user=self.user4, competition=self.competition4)
        CompetitionParticipant.objects.create(user=self.user2, competition=self.competition4)

        # Competition Five Participants
        CompetitionParticipant.objects.create(user=self.user1, competition=self.competition5)
        CompetitionParticipant.objects.create(user=self.user2, competition=self.competition5)
        CompetitionParticipant.objects.create(user=self.user3, competition=self.competition5)

        # Competition Six Participants
        CompetitionParticipant.objects.create(user=self.user1, competition=self.competition6)
        CompetitionParticipant.objects.create(user=self.user2, competition=self.competition6)
        CompetitionParticipant.objects.create(user=self.user3, competition=self.competition6)
        CompetitionParticipant.objects.create(user=self.user4, competition=self.competition6)

        # Competition Seven Participants
        CompetitionParticipant.objects.create(user=self.user1, competition=self.competition7)
        CompetitionParticipant.objects.create(user=self.user2, competition=self.competition7)
        CompetitionParticipant.objects.create(user=self.user3, competition=self.competition7)

    def test_front_page_competitions(self):
        popular_list = get_popular_competitions()
        featured_list = get_featured_competitions(excluded_competitions=popular_list)
        assert self.competition1 not in featured_list
        assert self.competition2 not in featured_list
        assert self.competition6 not in featured_list
        assert self.competition1 in popular_list
        assert self.competition2 in popular_list
        assert self.competition6 in popular_list
        assert len(popular_list) == 3
        assert len(featured_list) == 3
