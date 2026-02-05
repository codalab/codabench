from django.contrib import admin

from . import models


class LeaderboardExpansion(admin.ModelAdmin):
    list_display = ["id", "title", "submission_rule", "hidden"]
    search_fields = ["id", "title"]
    list_filter = ["hidden"]


class ColumExpansion(admin.ModelAdmin):
    raw_id_fields = ["leaderboard"]
    list_display = ["id", "title", "hidden"]
    search_fields = ["id", "title"]
    list_filter = ["hidden"]


class SubmissionScoreExpansion(admin.ModelAdmin):
    raw_id_fields = ["column"]
    list_display = ["id", "column", "score"]
    search_fields = ["id", "column"]


admin.site.register(models.Leaderboard, LeaderboardExpansion)
admin.site.register(models.Column, ColumExpansion)
admin.site.register(models.SubmissionScore, SubmissionScoreExpansion)
