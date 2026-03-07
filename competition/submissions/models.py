from django.db import models
from django.contrib.postgres.fields import JSONField

class Submission(models.Model):

    competition = models.ForeignKey("competitions.Competition", on_delete=models.CASCADE)

    # S3 storage path
    model_card_s3_key = models.CharField(max_length=500, null=True, blank=True)

    # Parser results
    model_card_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("PARSED", "Parsed"),
            ("FAILED", "Failed"),
        ],
        default="PENDING",
    )

    model_card_json = JSONField(null=True, blank=True)

    model_card_error = models.TextField(null=True, blank=True)