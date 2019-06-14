# # Todo: Implement ChahubSaveMixin on Submissions
# # Todo: Finish fixing tests
# import datetime
# from unittest import mock
#
# from django.conf import settings
# from django.test import TestCase
# from django.test.utils import override_settings
#
# from factories import UserFactory, CompetitionParticipantFactory, CompetitionFactory, PhaseFactory
#
#
# class ChahubUtillityTests(TestCase):
#     def setUp(self):
#         self.user = UserFactory(username='admin', password='test')
#         print('user created')
#         self.competition = CompetitionFactory()
#         print('competition created')
#         self.participant = CompetitionParticipantFactory(
#             user=self.user,
#             competition=self.competition,
#             status='approved'
#         )
#         print('participant created')
#         self.phase = PhaseFactory(
#             competition=self.competition,
#         )
#         print('phase created')
#
#     @override_settings(CHAHUB_API_URL='http://host.docker.internal/')
#     def test_send_to_chahub_utillity(self):
#         print('inside test file')
#         settings.PYTEST_FORCE_CHAHUB = True
#         with mock.patch('profiles.models.app.chahub.models.send_to_chahub') as send_to_chahub_mock:
#             send_to_chahub_mock.return_value = None
#             self.user.save()
#             assert send_to_chahub_mock.called
