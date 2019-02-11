import os
import socket

import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from time import sleep

from selenium.webdriver.chrome.webdriver import WebDriver
# from selenium.webdriver.firefox.webdriver import WebDriver


class CodalabTestHelpersMixin(object):

    def login(self, username, password):
        self.get(reverse('login'))

        self.find('input[name="username"]').send_keys(username)
        self.find('input[name="password"]').send_keys(password)
        self.find('.submit.button').click()


@pytest.mark.e2e
class SeleniumTestCase(CodalabTestHelpersMixin, StaticLiveServerTestCase):
    urls = 'urls'  # TODO: what the F is this???
    serialized_rollback = True

    host = '0.0.0.0'

    test_files_dir = f'{os.getcwd()}/src/tests/functional/test_files'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # options = Options()
        # options.add_argument('--headless')
        # cls.selenium = WebDriver(options=options)

        cls.host = socket.gethostbyname(socket.gethostname())

        d = DesiredCapabilities.FIREFOX
        d['loggingPrefs'] = {'browser': 'ALL'}

        cls.selenium = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            desired_capabilities=d,
        )

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
        return self.selenium.get(f'{self.live_server_url}{url}')

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

    def execute_script(self, script):
        return self.selenium.execute_script(script)

    @staticmethod
    def sleep(seconds):
        return sleep(seconds)

    # not supported in firefox
    # def print_log(self):
    #     for entry in self.selenium.get_log('browser'):
    #         print(entry)
