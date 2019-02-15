import os
import socket

import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from time import sleep
from utils.storage import BundleStorage, PublicStorage


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
        cls.host = socket.gethostbyname(socket.gethostname())
        cls.selenium = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.FIREFOX,
        )
        # Wait 10 seconds for elements to appear, always
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    @staticmethod
    def wait(seconds):
        return sleep(seconds)

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

    def execute_script(self, script):
        return self.selenium.execute_script(script)

    # ===========================================================
    # Assertion Helpers
    # ===========================================================
    def assert_current_url(self, url):
        assert self.selenium.current_url == f"{self.live_server_url}{url}"

    def assert_element_is_visible(self, selector):
        assert self.find(selector).is_displayed()

    @staticmethod
    def assert_storage_items_exist(*args):
        for item_name in args:
            assert BundleStorage.exists(item_name) or PublicStorage.exists(item_name)

    # ===========================================================
    # Cleanup Helpers
    # ===========================================================
    @staticmethod
    def remove_items_from_storage(*args):
        for item in args:
            PublicStorage.delete(item)
            BundleStorage.delete(item)
