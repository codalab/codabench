from django.urls import reverse

from factories import UserFactory
from ..utils import SeleniumTestCase


class TestLogin(SeleniumTestCase):

    def test_login(self):
        user = UserFactory(password="test")
        self.get(reverse("login"))
        self.find('input[name="username"]').send_keys(user.username)
        self.find('input[name="password"]').send_keys("test")
        self.find('.submit.button').click()
        self.assertCurrentUrl(reverse("pages:home"))
        self.screenshot()
        assert user.username in self.find("#user_dropdown .text").text
