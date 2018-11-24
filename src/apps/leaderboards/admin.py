from django.contrib import admin

from . import models


admin.site.register(models.Leaderboard)
admin.site.register(models.Column)
admin.site.register(models.SubmissionScore)
