from unittest import mock

from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import get_resolver

from factories import UserFactory
from utils import error_handlers


class ErrorPagesCloseDatabaseConnectionsTests(TestCase):
    """
    Under ASGI Django renders error pages in a thread that never closes its database connections.
    The error pages have to close them themselves, otherwise a connection that went away (for example
    after a database restart) breaks every later error page of a logged-in user with a 500.
    """

    def test_error_pages_use_the_connection_closing_handlers(self):
        resolver = get_resolver()

        assert resolver.resolve_error_handler(404) is error_handlers.page_not_found
        assert resolver.resolve_error_handler(403) is error_handlers.permission_denied

    def test_404_page_closes_database_connections(self):
        with mock.patch('utils.error_handlers.close_old_connections') as close_old_connections:
            response = self.client.get('/this-page-does-not-exist/')

        assert response.status_code == 404
        assert "Could not find the page you requested." in response.content.decode()
        close_old_connections.assert_called_once()

    def test_404_page_for_a_logged_in_user_closes_database_connections(self):
        user = UserFactory()
        self.client.force_login(user)

        with mock.patch('utils.error_handlers.close_old_connections') as close_old_connections:
            response = self.client.get('/this-page-does-not-exist/')

        assert response.status_code == 404
        assert user.username in response.content.decode()
        close_old_connections.assert_called_once()

    def test_403_page_closes_database_connections(self):
        request = RequestFactory().get('/forbidden/')
        request.user = AnonymousUser()

        with mock.patch('utils.error_handlers.close_old_connections') as close_old_connections:
            response = error_handlers.permission_denied(request, PermissionDenied())

        assert response.status_code == 403
        close_old_connections.assert_called_once()

    def test_database_connections_are_closed_even_if_rendering_fails(self):
        def failing_view(request, exception):
            raise Http404()

        request = RequestFactory().get('/missing/')

        with mock.patch('utils.error_handlers.close_old_connections') as close_old_connections:
            with self.assertRaises(Http404):
                error_handlers._close_db_connections_after(failing_view)(request, Http404())

        close_old_connections.assert_called_once()
