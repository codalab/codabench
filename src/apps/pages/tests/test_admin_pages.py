import uuid
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from factories import CompetitionFactory, PhaseFactory, QueueFactory, SubmissionFactory, UserFactory


class MonitorQueuesAccessTests(TestCase):

    def setUp(self):
        self.url = reverse('pages:monitor_queues')

    def test_logged_out_visitor_is_sent_to_login(self):
        """
        Opens the page without logging in.
        Expects a redirect to the login page.
        """
        response = self.client.get(self.url)

        assert response.status_code == 302
        assert reverse('accounts:login') in response.url

    def test_regular_user_is_refused(self):
        """
        Opens the page as a regular user.
        Expects a 403.
        """
        self.client.force_login(UserFactory())

        assert self.client.get(self.url).status_code == 403

    def test_staff_user_is_refused(self):
        """
        Opens the page as a staff user who is not a superuser.
        Expects a 403, because this page is for superusers only.
        """
        self.client.force_login(UserFactory(is_staff=True))

        assert self.client.get(self.url).status_code == 403

    def test_superuser_can_open_the_page(self):
        """
        Opens the page as a superuser.
        Expects the page with the worker monitor.
        """
        self.client.force_login(UserFactory(super_user=True))

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert "worker-monitor-toggle" in response.content.decode()


class AnalyticsAccessTests(TestCase):

    def setUp(self):
        self.url = reverse('analytics:analytics')

    def test_logged_out_visitor_is_sent_to_login(self):
        """
        Opens the page without logging in.
        Expects a redirect to the login page.
        """
        response = self.client.get(self.url)

        assert response.status_code == 302
        assert reverse('accounts:login') in response.url

    def test_regular_user_is_refused(self):
        """
        Opens the page as a regular user.
        Expects a 403.
        """
        self.client.force_login(UserFactory())

        assert self.client.get(self.url).status_code == 403

    def test_staff_user_is_refused(self):
        """
        Opens the page as a staff user who is not a superuser.
        Expects a 403, because this page is for superusers only.
        """
        self.client.force_login(UserFactory(is_staff=True))

        assert self.client.get(self.url).status_code == 403

    def test_superuser_can_open_the_page(self):
        """
        Opens the page as a superuser.
        Expects the page to load.
        """
        self.client.force_login(UserFactory(super_user=True))

        assert self.client.get(self.url).status_code == 200


class DjangoAdminAccessTests(TestCase):

    def setUp(self):
        self.url = reverse('admin:index')

    def test_logged_out_visitor_is_sent_to_admin_login(self):
        """
        Opens Django Admin without logging in.
        Expects a redirect to the admin login page.
        """
        response = self.client.get(self.url)

        assert response.status_code == 302
        assert reverse('admin:login') in response.url

    def test_regular_user_is_sent_to_admin_login(self):
        """
        Opens Django Admin as a regular user.
        Expects a redirect to the admin login page, and no admin content.
        """
        self.client.force_login(UserFactory())

        response = self.client.get(self.url)

        assert response.status_code == 302
        assert reverse('admin:login') in response.url

    def test_staff_user_can_open_it(self):
        """
        Opens Django Admin as a staff user.
        Expects the admin page.
        """
        self.client.force_login(UserFactory(is_staff=True))

        assert self.client.get(self.url).status_code == 200

    def test_superuser_can_open_it(self):
        """
        Opens Django Admin as a superuser.
        Expects the admin page.
        """
        self.client.force_login(UserFactory(super_user=True))

        assert self.client.get(self.url).status_code == 200


class ChangeUserAccessTests(TestCase):

    def setUp(self):
        self.url = reverse('su_login')

    def test_logged_out_visitor_is_redirected(self):
        """
        Opens Change User without logging in.
        Expects a redirect, and not the page.
        """
        assert self.client.get(self.url).status_code == 302

    def test_regular_user_is_redirected(self):
        """
        Opens Change User as a regular user.
        Expects a redirect, and not the page.
        """
        self.client.force_login(UserFactory())

        assert self.client.get(self.url).status_code == 302

    def test_staff_user_is_redirected(self):
        """
        Opens Change User as a staff user who is not a superuser.
        Expects a redirect, because only superusers can act as another user.
        """
        self.client.force_login(UserFactory(is_staff=True))

        assert self.client.get(self.url).status_code == 302

    def test_superuser_can_open_the_page(self):
        """
        Opens Change User as a superuser.
        Expects the page.
        """
        self.client.force_login(UserFactory(super_user=True))

        assert self.client.get(self.url).status_code == 200


class SubmissionStatusAccessTests(TestCase):

    def setUp(self):
        self.url = reverse('pages:server_status')

    def get_listed_submission_ids(self):
        """Open the page and return the ids of the submissions it lists."""
        response = self.client.get(self.url)
        return [submission.id for submission in response.context['submissions']]

    def create_queue_owned_by(self, user):
        """Create a queue. Why the mock: saving a queue would otherwise call the real RabbitMQ."""
        with mock.patch('queues.models.rabbit.create_queue', return_value=uuid.uuid4()):
            return QueueFactory(owner=user)

    def test_logged_out_visitor_is_sent_to_login(self):
        """
        Opens the page without logging in.
        Expects a redirect to the login page.
        """
        response = self.client.get(self.url)

        assert response.status_code == 302
        assert reverse('accounts:login') in response.url

    def test_regular_user_sees_only_own_submissions(self):
        """
        Opens the page as a user, with one submission of their own and one of another user.
        Expects only their own submission.
        """
        user = UserFactory()
        own_submission = SubmissionFactory(owner=user)
        SubmissionFactory()
        self.client.force_login(user)

        assert self.get_listed_submission_ids() == [own_submission.id]

    def test_superuser_sees_submissions_of_all_users(self):
        """
        Opens the page as a superuser, with submissions of two other users.
        Expects both submissions.
        """
        first_submission = SubmissionFactory()
        second_submission = SubmissionFactory()
        self.client.force_login(UserFactory(super_user=True))

        assert set(self.get_listed_submission_ids()) == {first_submission.id, second_submission.id}

    def test_competition_organizer_sees_submissions_to_their_competition(self):
        """
        Opens the page as the creator of a competition, with one submission to it and one elsewhere.
        Expects only the submission to their competition.
        """
        user = UserFactory()
        competition = CompetitionFactory(created_by=user)
        submission = SubmissionFactory(phase=PhaseFactory(competition=competition))
        SubmissionFactory()
        self.client.force_login(user)

        assert self.get_listed_submission_ids() == [submission.id]

    def test_competition_collaborator_sees_submissions_to_the_competition(self):
        """
        Opens the page as a collaborator of a competition, with one submission to it and one elsewhere.
        Expects only the submission to that competition.
        """
        user = UserFactory()
        competition = CompetitionFactory(collaborators=[user])
        submission = SubmissionFactory(phase=PhaseFactory(competition=competition))
        SubmissionFactory()
        self.client.force_login(user)

        assert self.get_listed_submission_ids() == [submission.id]

    def test_queue_owner_sees_submissions_on_their_queue(self):
        """
        Opens the page as the owner of a queue, with one submission on it and one elsewhere.
        Expects only the submission on their queue.
        """
        user = UserFactory()
        queue = self.create_queue_owned_by(user)
        submission = SubmissionFactory(queue=queue)
        SubmissionFactory()
        self.client.force_login(user)

        assert self.get_listed_submission_ids() == [submission.id]

    def test_queue_organizer_sees_submissions_on_the_queue(self):
        """
        Opens the page as an organizer of a queue, with one submission on it and one elsewhere.
        Expects only the submission on that queue.
        """
        user = UserFactory()
        queue = self.create_queue_owned_by(UserFactory())
        queue.organizers.add(user)
        submission = SubmissionFactory(queue=queue)
        SubmissionFactory()
        self.client.force_login(user)

        assert self.get_listed_submission_ids() == [submission.id]

    def test_staff_user_sees_only_own_submissions(self):
        """
        Opens the page as a staff user who is not a superuser, with one own submission and one of another user.
        Expects only their own submission, because seeing everything is for superusers.
        """
        user = UserFactory(is_staff=True)
        own_submission = SubmissionFactory(owner=user)
        SubmissionFactory()
        self.client.force_login(user)

        assert self.get_listed_submission_ids() == [own_submission.id]

    def test_soft_deleted_submissions_are_not_listed(self):
        """
        Opens the page as a user with one soft deleted submission.
        Expects no submissions.
        """
        user = UserFactory()
        SubmissionFactory(owner=user, is_soft_deleted=True)
        self.client.force_login(user)

        assert self.get_listed_submission_ids() == []

    def test_page_shows_the_left_bar_with_status_active(self):
        """
        Opens the page as a regular user.
        Expects the left bar with Submission Status marked as active.
        """
        self.client.force_login(UserFactory())

        content = self.client.get(self.url).content.decode()

        assert f'side-nav-link-active" href="{self.url}"' in content
