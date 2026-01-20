from django.contrib import admin

from . import models


class TaskExpansion(admin.ModelAdmin):
    raw_id_fields = [
        "created_by",
        "shared_with",
        "ingestion_program",
        "input_data",
        "reference_data",
        "scoring_program",
    ]
    list_display = [
        "id",
        "created_by",
        "name",
        "description",
        "ingestion_only_during_scoring",
        "is_public",
    ]
    list_filter = ["is_public", "ingestion_only_during_scoring"]
    search_fields = [
        "id",
        "name",
        "created_by__username",
    ]


class SolutionExpansion(admin.ModelAdmin):
    raw_id_fields = ["tasks", "data"]
    list_display = ["id", "name", "description", "data", "is_public"]
    list_filter = ["is_public"]
    search_fields = [
        "id",
    ]


admin.site.register(models.Task, TaskExpansion)
admin.site.register(models.Solution, SolutionExpansion)
