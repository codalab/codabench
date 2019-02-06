import os

import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.chrome.webdriver import WebDriver
# from selenium.webdriver.firefox.webdriver import WebDriver


class CodalabTestHelpersMixin(object):

    def login(self):
        self.get(reverse('login'))

        self.find("#id_username").send_keys("test")
        self.find("#id_password").send_keys("test")
        self.find("input[type='submit']").click()


@pytest.mark.e2e
class SeleniumTestCase(CodalabTestHelpersMixin, StaticLiveServerTestCase):
    # binary = FirefoxBinary('C://Program Files/Mozilla Firefox/firefox.exe')
    # driver = WebDriver(firefox_binary=binary)
    urls = 'urls'  # TODO: what the F is this???
    serialized_rollback = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        options = Options()
        options.add_argument('--headless')
        cls.selenium = WebDriver(options=options)

        # Wait 10 seconds for elements to appear, always
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.selenium.set_window_size(800, 600)

    def get(self, url):
        return self.selenium.get('%s%s' % (self.live_server_url, url))

    def find(self, selector):
        return self.selenium.find_element_by_css_selector(selector)

    def screenshot(self, name="screenshot.png"):
        self.selenium.get_screenshot_as_file(name)

    def circleci_screenshot(self, name="screenshot.png"):
        circle_dir = os.environ.get('CIRCLE_ARTIFACTS')
        assert circle_dir, "Could not find CIRCLE_ARTIFACTS environment variable!"
        self.screenshot(os.path.join(circle_dir, name))

    def assertCurrentUrl(self, url):
        assert self.selenium.current_url == f"{self.live_server_url}{url}"
