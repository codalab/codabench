from django.urls import reverse

from factories import UserFactory
from ..utils import SeleniumTestCase


class TestLogin(SeleniumTestCase):

    def test_login(self):
        user = UserFactory(password="test")
        self.login(username=user.username, password='test')
        self.assert_current_url(reverse("pages:home"))
        assert user.username in self.find("#user_dropdown .text").text
        self.circleci_screenshot(name='login.png')
