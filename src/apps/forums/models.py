import datetime

from django.db import models
from django.urls import reverse

from .helpers import send_mail


class Forum(models.Model):
    """
    Base Forum model.
    """
    competition = models.OneToOneField('competitions.Competition', unique=True, related_name="forum", on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('forums:forum_detail', kwargs={'forum_pk': self.pk})


class Thread(models.Model):
    """
    Base Thread Model. Allows user to keep track of a new post.
    """
    forum = models.ForeignKey('forums.Forum', related_name="threads", on_delete=models.CASCADE)
    date_created = models.DateTimeField()
    started_by = models.ForeignKey('profiles.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    last_post_date = models.DateTimeField(null=True, blank=True)
    pinned_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-last_post_date',)

    def save(self, *args, **kwargs):
        created = False
        if not self.id:
            # On first save do these actions
            self.date_created = datetime.datetime.today()
            created = True

        # Do the save THEN send email so we have an Id to work with
        super(Thread, self).save(*args, **kwargs)

        if created:
            if self.forum.competition.created_by.organizer_direct_message_updates:
                self.notify_user(self.forum.competition.created_by)

    def get_absolute_url(self):
        return reverse('forums:forum_thread_detail', kwargs={'forum_pk': self.forum.pk, 'thread_pk': self.pk})

    def notify_all_posters_of_new_post(self, post):
        """
        Notify users when a new post is created on the thread.
        """
        users_in_thread = set(post.posted_by for post in self.posts.all())

        for user in users_in_thread:
            if user != post.posted_by:
                self.notify_user(user, post=post)

    def notify_user(self, user, post=None):
        if user.allow_forum_notifications:
            send_mail(
                context={
                    'thread': self,
                    'user': user,
                    'new_post': self.posts.last() if post is None else post
                },
                subject='New post in %s' % self.title,
                html_file="forums/emails/new_post.html",
                text_file="forums/emails/new_post.txt",
                to_email=user.email
            )


class Post(models.Model):
    """
    Base Post model. Allows an authenticated user to post on a forum Thread.
    """
    thread = models.ForeignKey('forums.Thread', related_name="posts", on_delete=models.CASCADE)
    date_created = models.DateTimeField()
    posted_by = models.ForeignKey('profiles.User', on_delete=models.CASCADE)
    content = models.TextField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.date_created = datetime.datetime.today()
        return super(Post, self).save(*args, **kwargs)
