from django.db import models
from django.utils.timezone import now


class Announcement(models.Model):
    text = models.TextField(null=True, blank=True)


class NewsPost(models.Model):
    title = models.CharField(max_length=40)
    link = models.URLField(max_length=200, blank=True)
    created_when = models.DateTimeField(default=now)
    text = models.TextField(null=True, blank=True)
