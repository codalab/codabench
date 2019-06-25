from django.db import connections, DEFAULT_DB_ALIAS
from django.test.utils import CaptureQueriesContext
from django.urls import include, path, reverse, get_resolver
from rest_framework.test import APITestCase, URLPatternsTestCase

from factories import UserFactory, CompetitionFactory


class _AssertLessQueriesContext(CaptureQueriesContext):
    def __init__(self, test_case, num, connection):
        self.test_case = test_case
        self.num = num
        super().__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        executed = len(self)
        self.test_case.assertLess(
            executed, self.num,
            "%d queries executed, %d expected\nCaptured queries were:\n%s" % (
                executed, self.num,
                '\n'.join(
                    '%d. %s' % (i, query['sql']) for i, query in enumerate(self.captured_queries, start=1)
                )
            )
        )


class QueriesTestCase(APITestCase, URLPatternsTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.urls = [url for url in get_resolver(None).reverse_dict.keys() if isinstance(url, str)]
        self.list_urls = (string for string in self.urls if string.endswith('list'))
        self.detail_urls = (string for string in self.urls if string.endswith('detail'))

    def assertLessQueries(self, num, func=None, *args, using=DEFAULT_DB_ALIAS, **kwargs):
        conn = connections[using]

        context = _AssertLessQueriesContext(self, num, conn)
        if func is None:
            return context

        with context:
            func(*args, **kwargs)

    def gen_list_urls(self):
        return next(self.list_urls)

    def get_next_list_url(self):
        url = self.gen_list_urls()
        return self.client.get(reverse(url))

    def gen_detail_urls(self):
        return next(self.detail_urls)

    def get_next_detail_url(self):
        url = self.gen_detail_urls()
        # TODO: something here that can grab pks based maybe on url.strip('-detail') and grabbing an object w/ the name of what is left?
        return self.client.get(reverse(url))


class TestQueries(QueriesTestCase):
    urlpatterns = [
        path('api/', include('api.urls'))
    ]

    def setUp(self):
        self.user = UserFactory(username='admin', is_superuser=True)
        self.comp = CompetitionFactory()

    def test_list_query_count(self):
        self.client.login(username='admin', password='test')
        for _ in range(len([string for string in self.urls if string.endswith('list')])):
            self.assertLessQueries(5, self.get_next_list_url)

    # Todo: figure out how to handle detail views since they need PKs
    # def test_detail_query_count(self):
    #     self.client.login(username='admin', password='test')
    #     for _ in range(len([string for string in self.urls if string.endswith('detail')])):
    #         self.assertLessQueries(5, self.get_next_detail_url)
