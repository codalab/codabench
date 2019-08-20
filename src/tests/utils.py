import multiprocessing
import os
import socket
import traceback

import pytest
from channels.testing import ChannelsLiveServerTestCase
from daphne.endpoints import build_endpoint_description_strings
from daphne.server import Server
from daphne.testing import DaphneProcess
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from time import sleep

from twisted.internet import reactor

from utils.storage import BundleStorage, PublicStorage


class CodalabTestHelpersMixin(object):

    def login(self, username, password):
        self.get(reverse('accounts:login'))

        self.find('input[name="username"]').send_keys(username)
        self.find('input[name="password"]').send_keys(password)
        self.find('.submit.button').click()



class CodalabDaphneProcess(DaphneProcess):

    # have to set port in this hidden way so we can override it later (Daphne uses
    # fancy multiprocessing shared memory vars we have to work around
    _port = 36475

    def __init__(self, host, application, kwargs=None, setup=None, teardown=None):
        super().__init__(host, application, kwargs=None, setup=None, teardown=None)

        # Move our port into shared memory
        self.port.value = self._port

    def run(self):
        """Overriding this _just_ for the port bit...!"""
        try:
            # Create the server class -- with our fancy multiprocessing variable (note
            # `self.port.value`)
            endpoints = build_endpoint_description_strings(host=self.host, port=self.port.value)
            self.server = Server(
                application=self.application,
                endpoints=endpoints,
                signal_handlers=False,
                **self.kwargs
            )
            # Set up a poller to look for the port
            reactor.callLater(0.1, self.resolve_port)
            # Run with setup/teardown
            self.setup()
            try:
                self.server.run()
            finally:
                self.teardown()
        except Exception as e:
            # Put the error on our queue so the parent gets it
            self.errors.put((e, traceback.format_exc()))


@pytest.mark.e2e
class SeleniumTestCase(CodalabTestHelpersMixin, ChannelsLiveServerTestCase):
# class SeleniumTestCase(CodalabTestHelpersMixin, StaticLiveServerTestCase):
    urls = 'urls'  # TODO: what the F is this???
    serialized_rollback = True

    ProtocolServerProcess = CodalabDaphneProcess
    host = '0.0.0.0'
    serve_static = True

    # test_files_dir = f'{os.getcwd()}/src/tests/functional/test_files'
    test_files_dir = f'/test_files'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.host = socket.gethostbyname(socket.gethostname())
        cls.selenium = webdriver.Remote(
            command_executor=f'http://{settings.SELENIUM_HOSTNAME}:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.FIREFOX,
        )
        # Wait 10 seconds for elements to appear, always
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def wait(self, seconds):
        return sleep(seconds)

    def setUp(self):
        super().setUp()
        self.selenium.set_window_size(800, 600)

    def get(self, url):
        return self.selenium.get(f'{self.live_server_url}{url}')

    def find(self, selector):
        return self.selenium.find_element_by_css_selector(selector)

    def find_text_in_class(self, klass, text):
        return self.selenium.find_element_by_xpath(f"//*[@class='{klass}' and text()[contains(., '{text}')]]")

    def screenshot(self, name="screenshot.png"):
        self.selenium.get_screenshot_as_file(name)

    def circleci_screenshot(self, name="screenshot.png"):
        # TODO: Should the os.path.join() be outside the os.environ.get?
        circle_dir = os.environ.get('CIRCLE_ARTIFACTS', os.path.join(os.getcwd(), "artifacts/"))
        self.screenshot(os.path.join(circle_dir, name))
        os.chdir(circle_dir)

    def execute_script(self, script):
        return self.selenium.execute_script(script)

    # ===========================================================
    # Assertion Helpers
    # ===========================================================
    def assert_current_url(self, url):
        assert self.selenium.current_url == f"{self.live_server_url}{url}"

    def element_is_visible(self, selector):
        return self.find(selector).is_displayed()

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
