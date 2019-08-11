import os

from django.urls import reverse

from factories import UserFactory
from ..utils import SeleniumTestCase


class TestCompetitions(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(password='test')
        self.login(self.user.username, 'test')

    def test_competition_upload(self):
        self.get(reverse('competitions:upload'))
        self.circleci_screenshot(name='uploading_task.png')
        self.find('input[ref="file_input"]').send_keys(os.path.join(self.test_files_dir, 'competition.zip'))
        time = 0
        while time < 10 and not self.element_is_visible('div .ui.success.message'):
            self.wait(.5)
            time += .5
        assert self.element_is_visible('div .ui.success.message')
        comp = self.user.competitions.first()
        comp_url = reverse("competitions:detail", kwargs={"pk": comp.id})
        self.find(f'a[href="{comp_url}"]').click()
        self.assert_current_url(comp_url)
        task = comp.phases.first().tasks.first()
        created_items = [
            comp.bundle_dataset.data_file.name,
            comp.logo.name,
            task.scoring_program.data_file.name,
            task.reference_data.data_file.name,
        ]
        self.assert_storage_items_exist(*created_items)
        self.remove_items_from_storage(*created_items)
