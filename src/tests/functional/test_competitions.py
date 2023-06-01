import os
from datetime import datetime
from time import sleep

from django.urls import reverse

from factories import UserFactory
from selenium.webdriver.common.keys import Keys

from competitions.models import Competition
from tasks.models import Task
from ..utils import SeleniumTestCase

SHORT_WAIT = 0.2
LONG_WAIT = 4


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

    def test_upload_v18_competition(self):
        self._upload_competition('competition_18.zip')

    def test_upload_v2_competition(self):
        self._upload_competition('competition.zip')

    def test_manual_competition_creation(self):

        # Dataset Creation
        self.find('i[selenium="tasks"]').click()
        self.find('div[data-tab="datasets"]').click()
        self.find('i[selenium="add-dataset"]').click()
        self.find('input-text[selenium="scoring-name"] input').send_keys('sCoRiNg NaMe')
        self.find('input-text[selenium="scoring-desc"] input').send_keys('sCoRiNg DeScRiPtItIoN')
        self.execute_script('$("select[selenium=\'type\']").dropdown("set selected", "scoring_program")')
        self.find('input-file[selenium="file"] input').send_keys(os.path.join(self.test_files_dir, 'scoring_program.zip'))
        self.find('i[selenium="upload"]').click()
        sleep(LONG_WAIT)

        # Task Creation
        self.find('div[data-tab="tasks"]').click()
        self.find('div[selenium="create-task"]').click()
        self.find('input[selenium="name2"]').send_keys('nAmE')
        self.find('textarea[selenium="task-desc"]').send_keys('textbox')
        self.find('div[data-tab="data"]').click()
        self.find('input[id="scoring_program"]').send_keys('sco')
        sleep(LONG_WAIT)
        self.execute_script('$("div[selenium=\'scoring-program\'] a")[0].click()')
        self.find('div[selenium="save-task"]').click()

        # Details Tab
        competition_title = "selenium_test_comp"
        self.get(reverse('competitions:create'))
        self.find('input[ref="title"]').send_keys(competition_title)
        self.find('input[ref="logo"]').send_keys(os.path.join(self.test_files_dir, 'test_logo.png'))
        self.find('input[ref="docker_image"]').send_keys('docker_image')

        # Participation Tab
        self.find('a[data-tab="participation"]').click()
        self.execute_script('$("textarea[ref=\'terms\']")[0].EASY_MDE.value("pArTiCiPaTe")')
        sleep(LONG_WAIT)
        self.find('input[selenium="auto-approve"]').click()

        # Pages Tab
        self.find('a[data-tab="pages"]').click()
        self.find('i[class="add icon"]').click()
        self.find('input[selenium="title"]').send_keys('Title')
        self.execute_script('$("textarea[ref=\'content\']")[0].EASY_MDE.value("Testing123")')
        sleep(LONG_WAIT)
        self.find('div[selenium="save1"]').click()
        sleep(LONG_WAIT)

        # Phases Tab
        self.find('a[data-tab="phases"]').click()
        self.find('i[selenium="add-phase"]').click()
        sleep(LONG_WAIT)
        self.find('form[selenium="phase-form"] input[name="name"]').send_keys('Name')
        sleep(SHORT_WAIT)
        self.find('input[name="start"]').click()
        self.find('input[name="start"]').send_keys(2)
        self.find('input[name="start"]').send_keys(Keys.ENTER)
        self.find('input[name="end"]').send_keys(3)
        self.find('input[name="end"]').send_keys(Keys.ENTER)
        self.find('label[for="tasks"]').click()
        sleep(SHORT_WAIT)
        self.find("form[selenium='phase-form'] input.search").send_keys("Wheat")
        sleep(SHORT_WAIT)
        tasks = Task.objects.all()
        import random
        random_task = random.choice(tasks)
        task = random_task.key
        self.find(f"form[selenium='phase-form'] .menu .item[data-value='{task}']").click()
        self.execute_script('$("textarea[ref=\'description\']")[0].EASY_MDE.value("Testing123")')
        self.find('form[selenium="phase-form"] input[name="name"]').send_keys('Name')
        sleep(LONG_WAIT)
        self.find('div[selenium="save2"]').click()
        sleep(LONG_WAIT)

        # Leaderboard Tab
        leaderboard_title = 'tItLe'
        self.find('a[data-tab="leaderboard"]').click()
        self.find('i[selenium="add-leaderboard"]').click()
        self.find('input[selenium="title1"]').send_keys(leaderboard_title)
        self.find('input[selenium="key"]').send_keys('kEy')
        self.find('div[selenium="add-column"]').click()
        sleep(LONG_WAIT)
        self.find('input[selenium="column-key"]').send_keys('cOlUmN kEy')
        self.find('input[selenium="column-precision"]').send_keys('3')
        self.find('input[selenium="hidden"]').click()
        self.find('div[selenium="save3"]').click()
        sleep(LONG_WAIT)
        assert not Competition.objects.filter(title=competition_title).exists()
        self.find('button[selenium="save4"]').click()
        sleep(LONG_WAIT)
        assert Competition.objects.filter(title=competition_title).exists()
