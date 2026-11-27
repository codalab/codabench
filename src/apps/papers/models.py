from django.db import models, transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from utils.data import PathWrapper


class Paper(models.Model):
    doi = models.CharField(max_length=256, unique=True)
    title = models.CharField(max_length=256)
    authors = models.TextField(blank=True, default='')
    venue = models.CharField(max_length=256, blank=True, default='')
    publication_date = models.DateField(null=True, blank=True, db_index=True)
    citation_count = models.PositiveIntegerField(default=0, db_index=True)
    url = models.URLField(max_length=512, blank=True, default='')
    pdf_url = models.URLField(max_length=512, blank=True, default='')
    thumbnail = models.ImageField(upload_to=PathWrapper('paper_thumbnails'), null=True, blank=True)
    is_visible = models.BooleanField(default=True, db_index=True)
    created_when = models.DateTimeField(default=now)

    class Meta:
        ordering = ('-publication_date', '-citation_count', '-id')

    def __str__(self):
        year = self.publication_date.year if self.publication_date else 'n.d.'
        return f"{self.title} ({year})"

    @property
    def authors_summary(self):
        names = [n.strip() for n in self.authors.split(',') if n.strip()]
        if len(names) <= 2:
            return ', '.join(names)
        extra = len(names) - 2
        label = 'author' if extra == 1 else 'authors'
        return f"{', '.join(names[:2])} +{extra} {label}"


@receiver(post_delete, sender=Paper)
def delete_paper_thumbnail(sender, instance, **kwargs):
    # Remove the thumbnail from storage once the deletion commits so no orphan file is left behind
    if instance.thumbnail:
        storage = instance.thumbnail.storage
        name = instance.thumbnail.name
        transaction.on_commit(lambda: storage.delete(name))


@receiver(pre_save, sender=Paper)
def delete_replaced_paper_thumbnail(sender, instance, update_fields=None, **kwargs):
    # Clean up the old thumbnail from storage if it was cleared or replaced
    if not instance.pk or (update_fields is not None and 'thumbnail' not in update_fields):
        return
    old = Paper.objects.filter(pk=instance.pk).only('thumbnail').first()
    if old and old.thumbnail and old.thumbnail != instance.thumbnail:
        storage = old.thumbnail.storage
        name = old.thumbnail.name
        transaction.on_commit(lambda: storage.delete(name))
