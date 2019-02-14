from django.urls import reverse

from factories import UserFactory
from ..utils import SeleniumTestCase


class TestCompetitions(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(password='test')
        self.login(self.user.username, 'test')

    def test_task_solution_competition_upload(self):
        self.get(reverse('competitions:upload'))
        self.find('input[ref="file_input"]').send_keys(f'{self.test_files_dir}/task_competition.zip')
        self.wait(10)  # TODO: is there a better way to wait for comp to finish processing?
        self.assertElementExists('div .ui.success.message')
        comp = self.user.competitions.first()
        comp_url = reverse("competitions:detail", kwargs={"pk": comp.id})
        self.find(f'a[href="{comp_url}"]').click()
        self.assertCurrentUrl(comp_url)
        task = comp.phases.first().tasks.first()
        created_items = [
            comp.logo.name,
            task.scoring_program.data_file.name,
            task.reference_data.data_file.name,
            comp.phases.first().solutions.first().data.data_file.name,
        ]
        for item in created_items:
            # make sure element is there, and then delete it
            self.assertStorageItemExists(item)
        # TODO: this will delete datasets, how do we delete 'task_competition.zip'?
        self.removeFromStorage(*created_items)

    def test_legacy_competition_upload(self):
        self.get(reverse('competitions:upload'))
        self.find('input[ref="file_input"]').send_keys(f'{self.test_files_dir}/legacy_competition.zip')
        self.wait(10)  # TODO: is there a better way to wait for comp to finish processing?
        self.assertElementExists('div .ui.success.message')
        comp = self.user.competitions.first()
        comp_url = reverse("competitions:detail", kwargs={"pk": comp.id})
        self.find(f'a[href="{comp_url}"]').click()
        self.assertCurrentUrl(comp_url)
        created_items = [
            comp.phases.first().scoring_program.data_file.name,
            comp.logo.name
        ]
        for item in created_items:
            self.assertStorageItemExists(item)
        self.removeFromStorage(*created_items)
