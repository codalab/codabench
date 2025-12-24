from django.contrib import admin
from django.utils.translation import gettext_lazy as _
import json
import csv
from django.http import HttpResponse
from profiles.models import User
from . import models


class privateCompetitionsFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Private non-test")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "private"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ("privateSmall", _("Submissions >= 10 and Participants >= 5")),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Only show private competitions with >= 10 submissions and >=5 participants
        if self.value() == "privateSmall":
            return queryset.filter(
                published=False, submissions_count__gte=10, participants_count__gte=5
            )


# This will export the email of all the selected competition creators, removing duplications and banned users
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="email_username_list.csv"'
        },
    )
    writer = csv.writer(response)
    writer.writerow(
        [
            "Username",
            "Email",
            "Competition title",
            "Participants Count",
            "Submissions Count",
        ]
    )
    email_list = {}
    for obj in queryset:
        user = User.objects.get(id=obj.created_by_id)
        if not user.is_banned and user.email not in email_list.values():
            email_list.update({user.username: user.email})
            writer.writerow(
                [
                    user.username,
                    user.email,
                    obj.title,
                    obj.participants_count,
                    obj.submissions_count,
                ]
            )
    return response


# This will export the email of all the selected competition creators, removing duplications and banned users
def export_as_json(modeladmin, request, queryset):
    email_list = {}
    for obj in queryset:
        user = User.objects.get(id=obj.created_by_id)
        if not user.is_banned and user.email not in email_list.values():
            email_list.update({user.username: user.email})
    return HttpResponse(json.dumps(email_list), content_type="application/json")


class CompetitionExpansion(admin.ModelAdmin):
    search_fields = ["title", "docker_image", "created_by__username"]
    list_display = ["id", "title", "created_by", "is_featured"]
    list_display_links = ["id", "title"]
    actions = [export_as_json, export_as_csv]
    raw_id_fields = ["created_by", "collaborators", "queue"]
    list_filter = ["is_featured", privateCompetitionsFilter]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    ("title", "docker_image", "competition_type"),
                    "secret_key",
                    "terms",
                    "description",
                    "fact_sheet",
                    "contact_email",
                    "reward",
                    "report",
                    "submissions_count",
                    "participants_count",
                    "created_when",
                ]
            },
        ),
        ("Raw ID Fields", {"fields": ["created_by", "collaborators", "queue"]}),
        (
            "Checkboxes",
            {
                "fields": [
                    "published",
                    "registration_auto_approve",
                    "is_migrating",
                    "enable_detailed_results",
                    "show_detailed_results_in_submission_panel",
                    "show_detailed_results_in_leaderboard",
                    "make_programs_available",
                    "make_input_data_available",
                    "allow_robot_submissions",
                    "auto_run_submissions",
                    "can_participants_make_submissions_public",
                    "is_featured",
                    "forum_enabled",
                ]
            },
        ),
        ("Files", {"fields": ["logo", "logo_icon"]}),
    ]


class SubmissionExpansion(admin.ModelAdmin):
    # Raw Id Fields changes the field from displaying everything in a drop down menu into an id fields, which makes the page loads much faster (removes huge SELECT from the database)
    raw_id_fields = [
        "organization",
        "owner",
        "phase",
        "data",
        "task",
        "leaderboard",
        "participant",
        "queue",
        "created_by_migration",
        "parent",
        "scores",
    ]
    search_fields = ["owner__username"]
    list_display = [
        "id",
        "owner",
        "task",
        "is_public",
        "has_children",
        "is_soft_deleted",
    ]
    list_filter = ["is_public", "has_children", "is_soft_deleted"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    ("status", "ingestion_worker_hostname", "scoring_worker_hostname"),
                    "status_details",
                    "description",
                    "prediction_result_file_size",
                    "scoring_result_file_size",
                    "detailed_result_file_size",
                    "md5",
                    "secret",
                    "celery_task_id",
                    "name",
                    "fact_sheet_answers",
                    "created_when",
                    "started_when",
                    "soft_deleted_when",
                ],
            },
        ),
        (
            "Raw ID Fields",
            {
                "fields": [
                    "owner",
                    "organization",
                    "phase",
                    "data",
                    "task",
                    "leaderboard",
                    "participant",
                    "queue",
                    "created_by_migration",
                    "scores",
                    "parent",
                ],
            },
        ),
        (
            "Checkboxes",
            {
                "fields": [
                    "appear_on_leaderboards",
                    "is_public",
                    "is_specific_task_re_run",
                    "is_migrated",
                    "has_children",
                    "is_soft_deleted",
                ],
            },
        ),
        (
            "Files",
            {"fields": ["prediction_result", "scoring_result", "detailed_result"]},
        ),
    ]


class CompetitionCreationTaskStatusExpansion(admin.ModelAdmin):
    raw_id_fields = ["dataset", "created_by", "resulting_competition"]
    list_display = ["id", "created_by", "resulting_competition", "status"]
    search_fields = ["id", "created_by__username"]
    list_filter = ["status"]


class CompetitionParticipantExpansion(admin.ModelAdmin):
    raw_id_fields = ["user", "competition"]
    list_display = ["id", "user", "competition", "status"]
    list_filter = ["status"]
    search_fields = ["user__username", "competition"]


class PageExpansion(admin.ModelAdmin):
    raw_id_fields = ["competition"]
    list_display = ["id", "competition"]
    search_fields = ["competition", "content"]


class PhaseExpansion(admin.ModelAdmin):
    raw_id_fields = ["competition", "leaderboard", "public_data", "starting_kit"]
    list_display = ["id", "competition", "name"]
    search_fields = ["id", "competition", "name"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    ("name", "status", "execution_time_limit"),
                    ("max_submissions_per_day", "max_submissions_per_person"),
                    "index",
                    "description",
                    "start",
                    "end",
                ]
            },
        ),
        (
            "Raw ID Fields",
            {"fields": ["competition", "leaderboard", "public_data", "starting_kit"]},
        ),
        (
            "Checkboxes",
            {
                "fields": [
                    "is_final_phase",
                    "auto_migrate_to_this_phase",
                    "has_been_migrated",
                    "hide_output",
                    "hide_prediction_output",
                    "hide_score_output",
                    "has_max_submissions",
                ]
            },
        ),
    ]


admin.site.register(models.Competition, CompetitionExpansion)
admin.site.register(
    models.CompetitionCreationTaskStatus, CompetitionCreationTaskStatusExpansion
)
admin.site.register(models.CompetitionParticipant, CompetitionParticipantExpansion)
admin.site.register(models.Page, PageExpansion)
admin.site.register(models.Phase, PhaseExpansion)
admin.site.register(models.Submission, SubmissionExpansion)
