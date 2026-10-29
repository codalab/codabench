"""
Error page views that do not leave a database connection behind.

Under ASGI, Django builds the response for an exception (404, 403, ...) with
``sync_to_async(response_for_exception, thread_sensitive=False)``. That runs in a
worker thread of its own, outside of the request/response cycle that closes
connections, so a connection opened there (for example by the
``user.organizations.all`` query in ``base.html``, which only runs for logged-in
users) is kept by that thread forever. If the database restarts or drops the
connection, every later error page for a logged-in user fails with
``OperationalError: server closed the connection unexpectedly`` and turns into a
500, until the process is restarted. Pages that Django has to 404 or redirect
(``APPEND_SLASH``), like ``/competitions/12`` without the trailing slash, are
affected as well.

Closing the connections of the current thread once the error page is rendered
fixes that: a connection that is obsolete or unusable is dropped and the next
error page opens a fresh one.
"""
import functools

from django.db import close_old_connections
from django.views import defaults


def _close_db_connections_after(view):
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        finally:
            close_old_connections()

    return wrapper


page_not_found = _close_db_connections_after(defaults.page_not_found)
permission_denied = _close_db_connections_after(defaults.permission_denied)
