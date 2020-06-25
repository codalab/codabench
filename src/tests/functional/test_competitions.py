import os
from datetime import datetime
from time import sleep

from django.urls import reverse

from factories import UserFactory
from selenium.webdriver.common.keys import Keys

from ..utils import SeleniumTestCase
from tasks.models import Task


class TestCompetitions(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(password='test')
        self.login(self.user.username, 'test')

    def current_server_time_exists(self):
        # Get server time element
        element = self.find('#server_time')
        text = element.get_attribute('innerText')

        # Check that the text is a valid datetime by loading it with strptime.
        # This will raise a ValueError if the format is incorrect.
        assert datetime.strptime(text, '%B %d, %Y, %I:%M %p %Z')

    def _upload_competition(self, competition_zip_path):
        """Creates a competition and waits for success message.

        :param competition_zip_path: Relative to test_files/ dir
        """
        self.get(reverse('competitions:upload'))
        self.find('input[ref="file_input"]').send_keys(os.path.join(self.test_files_dir, competition_zip_path))
        self.circleci_screenshot(name='uploading_comp.png')

        assert self.element_is_visible('div .ui.success.message')

        comp = self.user.competitions.first()
        comp_url = reverse("competitions:detail", kwargs={"pk": comp.id})
        self.find(f'a[href="{comp_url}"]').click()
        self.assert_current_url(comp_url)
        self.current_server_time_exists()

    def test_upload_v15_competition(self):
        self._upload_competition('competition_15.zip')

    def test_upload_v2_competition(self):
        self._upload_competition('competition.zip')

    def test_manual_competition_creation(self):
        # Uploaded here to have taks to chose from on the phase page.
        self._upload_competition('competition.zip')
        tasks = Task.objects.all()
        import random
        random_task = random.choice(tasks)
        task = random_task.key
        self.get(reverse('competitions:create'))
        self.find('input[ref="title"]').send_keys('Title')

        self.find('input[ref="docker_image"]').send_keys('docker_image')

        self.find('a[data-tab="participation"]').click()
        self.execute_script('$("textarea[ref=\'terms\']")[0].EASY_MDE.value("pArTiCiPaTe")')


        self.find('a[data-tab="pages"]').click()
        self.find('i[class="add icon"]').click()
        self.find('input[selenium="title"]').send_keys('Title')
        self.execute_script('$("textarea[ref=\'content\']")[0].EASY_MDE.value("Testing123")')
        self.find('div[selenium="save1"]').click()
        sleep(1)

        self.find('a[data-tab="phases"]').click()
        self.find('i[selenium="add-phase"]').click()
        sleep(2)
        self.find('input[selenium="name1"]').send_keys('Name')
        sleep(2)
        self.find('input[name="start"]').click()
        self.find('input[name="start"]').send_keys(2)
        self.find('input[name="start"]').send_keys(Keys.ENTER)
        self.find('input[name="end"]').send_keys(3)
        self.find('input[name="end"]').send_keys(Keys.ENTER)

        s = f'$("form[selenium=\'phase-form\'] select[ref=\'multiselect\']").dropdown(\'set selected\', \'{task}\')'
        m = f'$("form[selenium=\'phase-form\'] select[ref=\'multiselect\']").dropdown(\'refresh\')'

        print(s)
        print(m)
        self.execute_script(s)
        self.execute_script(m)
        self.execute_script(f'toastr.error("{task}")')
        sleep(600)

        # self.execute_script('$("textarea[ref=\'description\']")[0].EASY_MDE.value("Testing123")')

        sleep(1)

        # self.find('a[data-tab="leaderboard"]').click()
        sleep(1)

        assert False
