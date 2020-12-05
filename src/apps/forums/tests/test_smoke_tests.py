from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from competitions.models import Competition
from ..models import Forum, Thread, Post


User = get_user_model()


class ForumSmokeTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser("admin", "admin@example.com", "pass")
        self.regular_user = User.objects.create_user("regular", email="regular@example.com", password="pass")

        self.competition = Competition.objects.create(
            title="Test Competition",
            created_by=self.admin_user,
            published=False,
        )
        self.forum = Forum.objects.create(competition=self.competition)
        self.thread = Thread.objects.create(forum=self.forum, started_by=self.regular_user)
        self.post = Post.objects.create(thread=self.thread, posted_by=self.regular_user)

    def test_forum_thread_list_view_returns_200(self):
        resp = self.client.get(reverse("forums:forum_detail", kwargs={'forum_pk': self.forum.pk}))
        self.assertEquals(resp.status_code, 200)

    def test_forum_post_new_thread_non_logged_in_returns_302(self):
        resp = self.client.get(reverse("forums:forum_new_thread", kwargs={'forum_pk': self.forum.pk}))
        self.assertEquals(resp.status_code, 302)

    def test_forum_post_new_thread_view_returns_200(self):
        self.client.login(username="regular", password="pass")
        resp = self.client.get(reverse("forums:forum_new_thread", kwargs={'forum_pk': self.forum.pk}))
        self.assertEquals(resp.status_code, 200)

    def test_forum_view_thread_returns_200(self):
        resp = self.client.get(reverse("forums:forum_thread_detail", kwargs={'forum_pk': self.forum.pk, 'thread_pk': self.thread.pk}))
        self.assertEquals(resp.status_code, 200)

    def test_forum_new_post_requires_login_returns_302(self):
        resp = self.client.get(reverse("forums:forum_new_post", kwargs={'forum_pk': self.forum.pk, 'thread_pk': self.thread.pk}))
        self.assertEquals(resp.status_code, 302)

    def test_forum_new_post_returns_200(self):
        self.client.login(username="regular", password="pass")
        resp = self.client.get(reverse("forums:forum_new_post", kwargs={'forum_pk': self.forum.pk, 'thread_pk': self.thread.pk}))
        self.assertEquals(resp.status_code, 200)

    def test_forum_delete_post_returns_200(self):
        self.client.login(username='admin', password='pass')
        resp = self.client.delete(reverse("forums:forum_delete_post", kwargs={'forum_pk': self.forum.pk, 'thread_pk': self.thread.pk, 'post_pk': self.post.pk}))
        self.assertEquals(resp.status_code, 302)

    def test_forum_delete_thread_returns_200(self):
        self.client.login(username='admin', password='pass')
        resp = self.client.delete(reverse("forums:forum_delete_thread", kwargs={'forum_pk': self.forum.pk, 'thread_pk': self.thread.pk}))
        self.assertEquals(resp.status_code, 302)
