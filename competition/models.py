from django.db import models
from django.contrib.postgres.fields import JSONField

class Competition(models.Model):

    MODEL_CARD_VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
    ]

    model_card_visibility = models.CharField(
        max_length=10,
        choices=MODEL_CARD_VISIBILITY_CHOICES,
        default="private",
    )