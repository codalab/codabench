import os
import socket
import traceback
from time import sleep

import pytest
from channels.testing import ChannelsLiveServerTestCase
from daphne.endpoints import build_endpoint_description_strings
from daphne.server import Server
from daphne.testing import DaphneProcess
from django.conf import settings
from django.urls import reverse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from twisted.internet import reactor

from competitions.models import Competition, Submission
from tasks.models import Solution, Task
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
    serialized_rollback = True

    ProtocolServerProcess = CodalabDaphneProcess
    host = '0.0.0.0'
    serve_static = True

    test_files_dir = f'/test_files'

    @classmethod
    def setUpClass(cls):
        """Note: setUpClass is only ran once at the start of testing, not before each test"""
        super().setUpClass()
        cls.host = socket.gethostbyname(socket.gethostname())
        cls.circle_dir = os.environ.get('CIRCLE_ARTIFACTS', os.path.join(os.getcwd(), "artifacts/"))

        # Setup console.log logging
        desired_capabilities = DesiredCapabilities.FIREFOX
        desired_capabilities['loggingPrefs'] = {'browser': 'ALL'}

        cls.selenium = webdriver.Remote(
            command_executor=f'http://{settings.SELENIUM_HOSTNAME}:4444/wd/hub',
            desired_capabilities=desired_capabilities,
        )

    @classmethod
    def tearDownClass(cls):
        """Note: tearDown is ran at the end of all testing"""
        cls.selenium.quit()
        super().tearDownClass()

    def tearDown(self):
        """Note: tearDown is ran after _every_ test"""
        self.remove_all_competition_data()
        super().tearDown()

    def wait(self, seconds):
        return sleep(seconds)

    def setUp(self):
        super().setUp()
        self.selenium.set_window_size(800, 600)

    def get(self, url):
        return self.selenium.get(f'{self.live_server_url}{url}')

    def find(self, selector, wait_time=10):
        try:
            wait = WebDriverWait(self.selenium, wait_time)
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except TimeoutException as e:
            self.circleci_screenshot(f'find_{selector}.png')
            raise e

    def find_text_in_class(self, klass, text, timeout=60):
        wait = WebDriverWait(self.selenium, timeout)
        return wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, klass), text))

    def screenshot(self, name="screenshot.png"):
        self.selenium.get_screenshot_as_file(name)

    def circleci_screenshot(self, name="screenshot.png"):
        self.screenshot(os.path.join(self.circle_dir, name))

    def execute_script(self, script):
        return self.selenium.execute_script(script)

    # ===========================================================
    # Assertion Helpers
    # ===========================================================
    def assert_current_url(self, url):
        wait = WebDriverWait(self.selenium, 10)
        wait.until(EC.url_to_be(f'{self.live_server_url}{url}'))
        assert self.selenium.current_url == f"{self.live_server_url}{url}", f'{self.selenium.current_url} != {self.live_server_url}{url}'

    def element_is_visible(self, selector):
        try:
            element = self.find(selector)
            wait = WebDriverWait(self.selenium, 60)
            element = wait.until(EC.visibility_of(element))
            return element.is_displayed()
        except TimeoutException as e:
            self.circleci_screenshot(f'{selector}_is_visible.png')
            raise e

    @staticmethod
    def assert_storage_items_exist(*args):
        for item_name in args:
            assert BundleStorage.exists(item_name) or PublicStorage.exists(item_name)

    # ===========================================================
    # Cleanup Helpers
    # ===========================================================
    def remove_all_competition_data(self):
        created_files = []

        # starting with competitions, then..
        for competition in Competition.objects.all():
            data_types = [
                'bundle_dataset',
                'logo',
            ]
            for data_type in data_types:
                file = getattr(competition, data_type, None)
                if file is not None:
                    created_files.append(file.name)

        # submissions
        for submission in Submission.objects.all():
            created_files += [
                submission.data.data_file.name,
                submission.prediction_result.name,
                submission.scoring_result.name,
            ]
            # submission logs
            for output in submission.details.all():
                created_files.append(output.data_file.name)

        # tasks and solutions
        for task in Task.objects.all():
            data_types = [
                'scoring_program',
                'ingestion_program',
                'input_data',
                'reference_data',
            ]
            for data_type in data_types:
                file = getattr(task, data_type, None)
                if file is not None:
                    created_files.append(file.data_file.name)

        for solution in Solution.objects.all():
            created_files.append(solution.data.data_file.name)

        self.assert_storage_items_exist(*created_files)
        self.remove_items_from_storage(*created_files)

    @staticmethod
    def remove_items_from_storage(*args):
        for item in args:
            PublicStorage.delete(item)
            BundleStorage.delete(item)
