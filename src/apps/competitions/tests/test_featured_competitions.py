from django.test import TestCase
from django.contrib.auth import get_user_model

from competitions.utils import get_featured_competitions, get_popular_competitions
from factories import CompetitionFactory, UserFactory, CompetitionParticipantFactory

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

        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.user3 = UserFactory()
        self.user4 = UserFactory()
        self.user5 = UserFactory()
        self.user6 = UserFactory()
        self.user7 = UserFactory()

        self.competition1 = CompetitionFactory(published=True)
        self.competition2 = CompetitionFactory(published=True)
        self.competition3 = CompetitionFactory(published=True)
        self.competition4 = CompetitionFactory(published=True)
        self.competition5 = CompetitionFactory(published=True)
        self.competition6 = CompetitionFactory(published=True)
        self.competition7 = CompetitionFactory(published=True)

        # Competition One Participants
        CompetitionParticipantFactory(user=self.user1, competition=self.competition1)
        CompetitionParticipantFactory(user=self.user2, competition=self.competition1)
        CompetitionParticipantFactory(user=self.user3, competition=self.competition1)
        CompetitionParticipantFactory(user=self.user4, competition=self.competition1)
        CompetitionParticipantFactory(user=self.user5, competition=self.competition1)
        CompetitionParticipantFactory(user=self.user6, competition=self.competition1)
        CompetitionParticipantFactory(user=self.user7, competition=self.competition1)

        # Competition Two Participants
        CompetitionParticipantFactory(user=self.user1, competition=self.competition2)
        CompetitionParticipantFactory(user=self.user2, competition=self.competition2)
        CompetitionParticipantFactory(user=self.user3, competition=self.competition2)
        CompetitionParticipantFactory(user=self.user4, competition=self.competition2)
        CompetitionParticipantFactory(user=self.user5, competition=self.competition2)

        # Competition Three Participants
        CompetitionParticipantFactory(user=self.user4, competition=self.competition3)
        CompetitionParticipantFactory(user=self.user2, competition=self.competition3)
        CompetitionParticipantFactory(user=self.user3, competition=self.competition3)

        # Competition Four Participants
        CompetitionParticipantFactory(user=self.user4, competition=self.competition4)
        CompetitionParticipantFactory(user=self.user2, competition=self.competition4)

        # Competition Five Participants
        CompetitionParticipantFactory(user=self.user1, competition=self.competition5)
        CompetitionParticipantFactory(user=self.user2, competition=self.competition5)
        CompetitionParticipantFactory(user=self.user3, competition=self.competition5)

        # Competition Six Participants
        CompetitionParticipantFactory(user=self.user1, competition=self.competition6)
        CompetitionParticipantFactory(user=self.user2, competition=self.competition6)
        CompetitionParticipantFactory(user=self.user3, competition=self.competition6)
        CompetitionParticipantFactory(user=self.user4, competition=self.competition6)

        # Competition Seven Participants
        CompetitionParticipantFactory(user=self.user1, competition=self.competition7)
        CompetitionParticipantFactory(user=self.user2, competition=self.competition7)
        CompetitionParticipantFactory(user=self.user3, competition=self.competition7)

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
