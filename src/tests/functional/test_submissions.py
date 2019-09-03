import os
import uuid
from unittest import mock

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from competitions.models import Submission
from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory, PhaseFactory
from ..utils import SeleniumTestCase


class TestSubmissions(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(password='test')
        # self.competition = CompetitionFactory(created_by=self.user, published=True)
        # self.phase = PhaseFactory(competition=self.competition)
        # CompetitionParticipantFactory(user=self.user, competition=self.competition, status='approved')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_submission_appears_in_submissions_table(self):
        self.login(username=self.user.username, password='test')

        self.get(reverse('competitions:upload'))
        with self.implicit_wait_context(60):
            self.find('input[ref="file_input"]').send_keys(os.path.join(self.test_files_dir, 'competition.zip'))

        assert self.element_is_visible('div .ui.success.message')

        competition = self.user.competitions.first()
        comp_url = reverse("competitions:detail", kwargs={"pk": competition.id})
        self.find(f'a[href="{comp_url}"]').click()
        self.assert_current_url(comp_url)

        self.circleci_screenshot("set_submission_file_name.png")
        with self.implicit_wait_context(60):
            self.find('input[ref="file_input"]').send_keys(os.path.join(self.test_files_dir, 'submission.zip'))
        self.circleci_screenshot(name='uploading_submission.png')

        with self.implicit_wait_context(60):
            assert self.element_is_visible('#output-modal')

        assert self.find_text_in_class('.submission_output', 'Scores')
        assert self.find_text_in_class('.submission_output', 'accuracy')

        self.execute_script("$('#output-modal').modal('hide')")
        assert self.find('submission-manager table tbody tr:nth-of-type(1) td:nth-of-type(2)').text == 'submission.zip'

        submission = self.user.submission.first()
        task = competition.phases.first().tasks.first()
        created_files = [
            # Competition related files
            competition.bundle_dataset.data_file.name,
            competition.logo.name,
            task.scoring_program.data_file.name,
            task.reference_data.data_file.name,

            # Submission related files
            submission.data.data_file.name,
            submission.prediction_result.name,
            submission.scoring_result.name,
        ]
        for detail in submission.details.all():
            created_files.append(detail.data_file.name)

        self.assert_storage_items_exist(*created_files)
        self.remove_items_from_storage(*created_files)
