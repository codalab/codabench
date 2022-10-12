from django.conf import settings
# from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone
from pyrabbit2.http import HTTPError

from queues import rabbit


class Queue(models.Model):
    name = models.CharField(max_length=64)
    vhost = models.UUIDField(unique=True)
    is_public = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='queues',
        blank=True,
        null=True
    )
    organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='organized_queues',
        blank=True,
    )
    created_when = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    @property
    def broker_url(self):
        # host = Site.objects.get_current().domain
        if self.owner:
            return f"pyamqp://{self.owner.rabbitmq_username}:{self.owner.rabbitmq_password}@{settings.DOMAIN_NAME}:{settings.RABBITMQ_PORT}/{self.vhost}"

    def delete(self, *args, **kwargs):
        try:
            rabbit.delete_vhost(str(self.vhost))
        except HTTPError:
            # Vhost not found or something
            pass
        return super().delete(*args, **kwargs)

    def save(self, create_queue=True, **kwargs):
        if not self.vhost and create_queue:
            self.vhost = rabbit.create_queue(self.owner)
        super().save(**kwargs)
