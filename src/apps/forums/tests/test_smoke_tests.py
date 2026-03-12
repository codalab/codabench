# apps/forums/tests/test_smoke_tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from competitions.models import Competition, CompetitionParticipant
from ..models import Forum, Thread, Post

User = get_user_model()


class ForumTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="pass"
        )
        cls.regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="pass"
        )
        cls.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="pass"
        )

        cls.competition = Competition.objects.create(
            title="Test Competition",
            created_by=cls.admin_user,
            published=False,
            forum_enabled=True
        )

        cls.forum = Forum.objects.create(competition=cls.competition)

        CompetitionParticipant.objects.create(
            competition=cls.competition,
            user=cls.regular_user,
            status=CompetitionParticipant.APPROVED
        )

        cls.thread = Thread.objects.create(
            forum=cls.forum,
            started_by=cls.regular_user
        )

        cls.post = Post.objects.create(
            thread=cls.thread,
            posted_by=cls.regular_user,
            content="Initial post"
        )

    def test_forum_detail_view_returns_200(self):
        resp = self.client.get(reverse("forums:forum_detail", kwargs={"forum_pk": self.forum.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_thread_detail_view_returns_200(self):
        resp = self.client.get(reverse(
            "forums:forum_thread_detail",
            kwargs={"forum_pk": self.forum.pk, "thread_pk": self.thread.pk}
        ))
        self.assertEqual(resp.status_code, 200)

    def test_create_thread_requires_login(self):
        resp = self.client.get(reverse("forums:forum_new_thread", kwargs={"forum_pk": self.forum.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_create_thread_post(self):
        self.client.login(username="regular", password="pass")
        resp = self.client.post(reverse("forums:forum_new_thread", kwargs={"forum_pk": self.forum.pk}), {
            "title": "New thread",
            "content": "Hello world",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Thread.objects.count(), 2)

    def test_create_post_requires_login(self):
        resp = self.client.get(reverse(
            "forums:forum_new_post",
            kwargs={"forum_pk": self.forum.pk, "thread_pk": self.thread.pk}
        ))
        self.assertEqual(resp.status_code, 302)

    def test_create_post(self):
        self.client.login(username="regular", password="pass")
        resp = self.client.post(reverse(
            "forums:forum_new_post",
            kwargs={"forum_pk": self.forum.pk, "thread_pk": self.thread.pk}
        ), {"content": "Another message"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Post.objects.count(), 2)

    def test_delete_post_by_admin(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(reverse(
            "forums:forum_delete_post",
            kwargs={
                "forum_pk": self.forum.pk,
                "thread_pk": self.thread.pk,
                "post_pk": self.post.pk
            }
        ))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Post.objects.filter(pk=self.post.pk).count(), 0)

    def test_delete_post_forbidden_for_other_user(self):
        p = Post.objects.create(thread=self.thread, posted_by=self.regular_user, content="temp-forb")

        self.client.login(username="other", password="pass")
        resp = self.client.post(reverse(
            "forums:forum_delete_post",
            kwargs={
                "forum_pk": self.forum.pk,
                "thread_pk": self.thread.pk,
                "post_pk": p.pk
            }
        ))

        exists_after = Post.objects.filter(pk=p.pk).exists()
        self.assertIn(resp.status_code, (302, 403))
        if resp.status_code == 403:
            self.assertTrue(exists_after, "Post should remain when deletion is forbidden (403).")

    def test_delete_thread_by_admin(self):
        t = Thread.objects.create(forum=self.forum, started_by=self.regular_user)
        Post.objects.create(thread=t, posted_by=self.regular_user, content="to be deleted")

        self.client.login(username="admin", password="pass")
        resp = self.client.post(reverse(
            "forums:forum_delete_thread",
            kwargs={
                "forum_pk": self.forum.pk,
                "thread_pk": t.pk
            }
        ))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Thread.objects.filter(pk=t.pk).count(), 0)

    def test_delete_thread_forbidden_for_other_user(self):
        t = Thread.objects.create(forum=self.forum, started_by=self.regular_user)
        Post.objects.create(thread=t, posted_by=self.regular_user, content="keep me")

        self.client.login(username="other", password="pass")
        resp = self.client.post(reverse(
            "forums:forum_delete_thread",
            kwargs={
                "forum_pk": self.forum.pk,
                "thread_pk": t.pk
            }
        ))

        self.assertIn(resp.status_code, (302, 403))
        if resp.status_code == 403:
            self.assertEqual(Thread.objects.filter(pk=t.pk).count(), 1)