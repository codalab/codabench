from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from pyrabbit.http import HTTPError

from apps.queues import rabbit


class Queue(models.Model):
    name = models.CharField(max_length=64)
    vhost = models.UUIDField(unique=True)
    is_public = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name='queues',
        blank=True,
        null=True
    )
    organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='organized_queues',
        blank=True,
        help_text="(Organizers allowed to view this queue when they assign their competition to a queue)"
    )

    def __str__(self):
        return self.name

    @property
    def broker_url(self):
        host = Site.objects.get_current().domain
        if self.owner:
            return f"pyamqp://{self.owner.rabbitmq_username}:{self.owner.rabbitmq_password}@{host}/{self.vhost}"

    def delete(self, using=None):
        try:
            rabbit.delete_vhost(str(self.vhost))
        except HTTPError:
            # Vhost not found or something
            pass
        return super(Queue, self).delete(using)
