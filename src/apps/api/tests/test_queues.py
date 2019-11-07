import uuid
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from factories import UserFactory, QueueFactory
from queues.models import Queue


class QueuesAPITestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.another_user = UserFactory(username='another_user')
        self.collab_user = UserFactory(username='organizer_user')
        self.created_queue = self.mock_create_queue(owner=self.user, name='TestUserQueue')
        self.created_queue.organizers.add(self.collab_user)

    def _get_test_update_data(self, return_id=True):
        data = {
            'name': 'A BRAND NEW NAME',
            'owner': self.user.id,
            'is_public': False,
        }
        if return_id:
            data['id'] = self.created_queue.id
        return data

    def mock_create_queue(self, **kwargs):
        # Prevent queue creation
        with mock.patch('queues.models.rabbit.create_queue') as rabbit_create_queue:
            rabbit_create_queue.return_value = uuid.uuid4()
            return QueueFactory(**kwargs)

    def queue_api_request_with_mock(self, http_method, url_name, url_kwargs, data):
        # So we can make API requests without triggering rabbitmq actual queue creation
        with mock.patch('queues.models.rabbit.create_queue') as rabbit_create_queue:
            rabbit_create_queue.return_value = uuid.uuid4()
            response = getattr(self.client, http_method)(
                reverse(url_name, kwargs=url_kwargs),
                data=data,
                content_type='application/json'
            )
            return response, rabbit_create_queue.called

    def test_create_queue_through_api(self):
        self.client.login(username='test', password='test')
        assert Queue.objects.count() == 1
        data = {
            'name': 'A brand new queue',
            'owner': self.user.id,
            'is_public': False,
            'id': self.created_queue.id
        }
        response, rabbit_create_queue_called = self.queue_api_request_with_mock('post', 'queues-list', {}, data)
        assert rabbit_create_queue_called
        assert Queue.objects.count() == 2
        assert response.status_code == 201

    # --------- Permission tests ---------

    def test_organizer_can_perform_all_operations(self):
        self.client.login(username='test', password='test')
        response, _ = self.queue_api_request_with_mock(
            'put',
            'queues-detail',
            {'pk': self.created_queue.id},
            self._get_test_update_data()
        )
        assert response.status_code == 200
        assert Queue.objects.get(pk=self.created_queue.id).name == 'A BRAND NEW NAME'

        response, _ = self.queue_api_request_with_mock(
            'delete',
            'queues-detail',
            {'pk': self.created_queue.id},
            {}
        )
        assert response.status_code == 204
        assert not Queue.objects.filter(pk=self.created_queue.id).exists()

    def test_other_user_cannot_delete_or_edit_queue(self):
        self.client.login(username='another_user', password='another_user')
        response, _ = self.queue_api_request_with_mock(
            'put',
            'queues-detail',
            {'pk': self.created_queue.id},
            self._get_test_update_data()
        )
        assert response.status_code == 403
        assert Queue.objects.get(pk=self.created_queue.id).name != 'A BRAND NEW NAME'

        response, _ = self.queue_api_request_with_mock(
            'delete',
            'queues-detail',
            {'pk': self.created_queue.id},
            {}
        )

        assert response.status_code == 403
        assert Queue.objects.filter(pk=self.created_queue.id).exists()

    def test_collab_user_cannot_delete_or_edit_queue(self):
        self.client.login(username='organizer_user', password='organizer_user')
        response, _ = self.queue_api_request_with_mock(
            'put',
            'queues-detail',
            {'pk': self.created_queue.id},
            self._get_test_update_data()
        )
        assert response.status_code == 403
        assert Queue.objects.get(pk=self.created_queue.id).name != 'A BRAND NEW NAME'

        response, _ = self.queue_api_request_with_mock(
            'delete',
            'queues-detail',
            {'pk': self.created_queue.id},
            {}
        )

        assert response.status_code == 403
        assert Queue.objects.filter(pk=self.created_queue.id).exists()

    # --------- Queue Limit Tests ---------

    # Test user queue limits
    def test_queue_limits_for_regular_users(self):
        self.user.rabbitmq_queue_limit = 1
        response, _ = self.queue_api_request_with_mock(
            'post',
            'queues-list',
            {},
            self._get_test_update_data(return_id=False)
        )
        assert response.status_code == 403
        assert self.user.rabbitmq_queue_limit == self.user.queues.count()

    # Test super user queue limits
    def test_super_users_has_no_queue_limit(self):
        # Make test user a superuser before hand
        self.user.is_superuser = True
        self.user.rabbitmq_queue_limit = 2
        self.user.save()

        self.mock_create_queue(owner=self.user)
        assert self.user.queues.count() == self.user.rabbitmq_queue_limit

        self.client.login(username='test', password='test')
        response, rabbit_create_queue_called = self.queue_api_request_with_mock(
            'post',
            'queues-list',
            {},
            self._get_test_update_data(return_id=False)
        )
        assert rabbit_create_queue_called
        assert response.status_code == 201

    # --------- Filter Test ---------
    def test_public_filter_does_not_exclude_own_users_public_queues_and_search_works(self):
        # Create a public queue we want to show in our results by search/public=True
        self.mock_create_queue(owner=self.another_user, name='TestPublicQueue', is_public=True)

        # Create another queue we do not want to show up that is not public, and should not return in results
        self.mock_create_queue(owner=self.another_user)

        # Create yet another queue that IS public, that we want filtered out by search
        self.mock_create_queue(owner=self.another_user, is_public=True)

        self.client.login(username='test', password='test')

        response = self.client.get(f"{reverse('queues-list')}?search=test&public=True")
        assert response.status_code == 200
        assert len(response.json()['results']) == 2
        assert response.json()['results'][0]['name'] == 'TestPublicQueue'
        assert response.json()['results'][0]['is_public']
        assert response.json()['results'][1]['name'] == 'TestUserQueue'
        assert not response.json()['results'][1]['is_public']
