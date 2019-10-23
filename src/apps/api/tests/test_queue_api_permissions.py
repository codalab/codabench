import uuid
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from factories import UserFactory
from queues.models import Queue


class QueuesAPITestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.another_user = UserFactory(username='another_user')
        self.organizer_user = UserFactory(username='organizer_user')
        # Prevent queue creation
        with mock.patch('queues.models.rabbit.create_queue') as rabbit_create_queue:
            rabbit_create_queue.return_value = uuid.uuid4()
            self.created_queue = Queue.objects.create(
                owner=self.user,
                name='Test Queue',
                is_public=False,
            )
        self.created_queue.organizers.add(self.organizer_user)

    def test_create_queue_through_api(self):
        self.client.login(username='test', password='test')
        my_new_vhost = uuid.uuid4()
        with mock.patch('queues.models.rabbit.create_queue') as rabbit_create_queue:
            rabbit_create_queue.return_value = my_new_vhost
            response = self.client.post(
                reverse('queues-list'),
                data={
                    'name': 'A brand new queue',
                    'owner': self.user.id,
                    'is_public': False,
                    'id': self.created_queue.id
                },
                content_type='application/json'
            )
            assert rabbit_create_queue.called
        assert Queue.objects.filter(vhost=my_new_vhost).exists()
        assert response.status_code == 201

    def test_organizer_can_perform_all_operations(self):
        self.client.login(username='test', password='test')
        response = self.client.put(
            reverse('queues-detail', kwargs={'pk': self.created_queue.id}),
            data={
                'name': 'A BRAND NEW NAME',
                'owner': self.user.id,
                'is_public': False,
                'id': self.created_queue.id
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        assert Queue.objects.get(pk=self.created_queue.id).name == 'A BRAND NEW NAME'

        response = self.client.delete(
            reverse('queues-detail', kwargs={'pk': self.created_queue.id}),
        )
        assert response.status_code == 204
        assert not Queue.objects.filter(pk=self.created_queue.id).exists()

    def test_other_user_cannot_delete_or_edit_queue(self):
        self.client.login(username='another_user', password='another_user')
        response = self.client.put(
            reverse('queues-detail', kwargs={'pk': self.created_queue.id}),
            data={
                'name': 'A BRAND NEW NAME',
                'owner': self.user.id,
                'is_public': False,
                'id': self.created_queue.id
            },
            content_type='application/json'
        )
        assert response.status_code != 200
        assert Queue.objects.get(pk=self.created_queue.id).name != 'A BRAND NEW NAME'

        response = self.client.delete(
            reverse('queues-detail', kwargs={'pk': self.created_queue.id}),
        )
        assert response.status_code != 204
        assert Queue.objects.filter(pk=self.created_queue.id).exists()

    def test_organizer_user_cannot_delete_or_edit_queue(self):
        self.client.login(username='another_user', password='another_user')
        response = self.client.put(
            reverse('queues-detail', kwargs={'pk': self.created_queue.id}),
            data={
                'name': 'A BRAND NEW NAME',
                'owner': self.user.id,
                'is_public': False,
                'id': self.created_queue.id
            },
            content_type='application/json'
        )
        assert response.status_code != 200
        assert Queue.objects.get(pk=self.created_queue.id).name != 'A BRAND NEW NAME'

        response = self.client.delete(
            reverse('queues-detail', kwargs={'pk': self.created_queue.id}),
        )
        assert response.status_code != 204
        assert Queue.objects.filter(pk=self.created_queue.id).exists()
