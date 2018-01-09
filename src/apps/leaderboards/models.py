from django.conf import settings
from django.db import models
from django.utils import timezone

from competitions.models import Competition
from settings.base import BundleStorage
from utils.data import PathWrapper


class Leaderboard(models.Model):
    competition = models.OneToOneField(Competition, related_name='leaderboard', on_delete=models.DO_NOTHING, null=True, blank=True)
    column_count = models.IntegerField(default=0, blank=False, null=False)
    main_column = models.OneToOneField('Column', related_name='attached_leaderboard', blank=True, null=True,
                                       on_delete=models.SET_NULL)

    def __str__(self):
        return "leaderboard-{0}-{1}-{2}".format(self.name, self.pk, self.competition.title)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        count = 0
        for column in self.columns.all():
            count += 1
        self.column_count = count
        # If we don't have a main column when we save, set it to the first one we have.
        if not self.main_column or self.main_column is None:
            if len(self.columns.all()) > 1:
                self.main_column = self.columns.all()[0]
        super(Leaderboard, self).save()


class Metric(models.Model):
    name = models.CharField(max_length=50, blank=False, default='')
    description = models.CharField(max_length=50, blank=False, default=timezone.now)
    key = models.CharField(max_length=10, unique=True, blank=False, null=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_metrics', on_delete=models.DO_NOTHING)

    def __str__(self):
        return "metric-{0}-{1}".format(self.name, self.pk)


class Column(models.Model):
    name = models.CharField(max_length=50, blank=False, default='new_metric')
    metric = models.ForeignKey(Metric, related_name='columns', on_delete=models.DO_NOTHING)
    leaderboard = models.ForeignKey(Leaderboard, related_name='columns', blank=True, null=True,
                                    on_delete=models.SET_NULL)

    def __str__(self):
        return "column-{0}-{1}".format(self.name, self.pk)
