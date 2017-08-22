from django.db import models


class Competition(models.Model):
    title = models.CharField(max_length=256)
