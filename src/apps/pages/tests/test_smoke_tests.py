from django.test import TestCase
from django.urls import reverse


class SmokeTests(TestCase):

    def test_front_page(self):
        assert self.client.get(reverse('pages:home')).status_code == 200
