from django.contrib import admin
from django.utils.translation import gettext_lazy as _
import json
import csv
from django.http import HttpResponse
from profiles.models import User
from . import models


# General class used to make custom filter
class InputFilter(admin.SimpleListFilter):
    template = "admin/input_filter.html"

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice["query_parts"] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class SubmissionsCountFilter(InputFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("≥ Submissions Count (Greater than or Equal to)")
    # Parameter for the filter that will be used in the URL query.
    parameter_name = "submissions_count_gte"

    def queryset(self, request, queryset):
        if self.value() is not None:
            value = self.value()
            return queryset.filter(submissions_count__gte=value)


class ParticipantsCountFilter(InputFilter):
    title = _("≥ Participants Count (Greater Than or Equal to)")
    parameter_name = "participants_count_gte"

    def queryset(self, request, queryset):
        if self.value() is not None:
            value = self.value()
            return queryset.filter(participants_count__gte=value)


# This will export the email of all the selected competition creators, removing duplications and banned users
@admin.display(description="Export as CSV")
def CompetitionExport_as_csv(modeladmin, request, queryset):
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


@admin.display(description="Export as CSV")
def SubmissionsExport_as_csv(modeladmin, request, queryset):
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="submissions.csv"'},
    )
    writer = csv.writer(response)
    writer.writerow(["ID", "Owner", "Status", "Task", "Phase", "Queue"])
    for obj in queryset:
        writer.writerow([obj.id, obj.owner, obj.status, obj.task, obj.phase, obj.queue])
    return response


# This will export the email of all the selected competition creators, removing duplications and banned users
@admin.display(description="Export as JSON")
def CompetitionExport_as_json(modeladmin, request, queryset):
    email_list = {}
    for obj in queryset:
        user = User.objects.get(id=obj.created_by_id)
        if not user.is_banned and user.email not in email_list.values():
            email_list.update({user.username: user.email})
    return HttpResponse(json.dumps(email_list), content_type="application/json")


class QueueFilter(InputFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Queue (default for Default Queue)")
    # Parameter for the filter that will be used in the URL query.
    parameter_name = "queue"

    def queryset(self, request, queryset):
        if self.value() is not None:
            value = self.value()
            if value.lower() == "default":
                return queryset.filter(queue__name__isnull=True)
            else:
                return queryset.filter(queue__name=value)


class CompetitionExpansion(admin.ModelAdmin):
    search_fields = ["id", "title", "docker_image", "created_by__username"]
    list_display = ["id", "title", "created_by", "published", "is_featured"]
    list_display_links = ["id", "title"]
    actions = [CompetitionExport_as_json, CompetitionExport_as_csv]
    raw_id_fields = ["created_by", "collaborators", "queue"]
    list_filter = [
        "published",
        "is_featured",
        ParticipantsCountFilter,
        SubmissionsCountFilter,
        QueueFilter,
    ]
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


class CompetitionOrganizerFilter(InputFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Competition Organizer")
    # Parameter for the filter that will be used in the URL query.
    parameter_name = "organizer"

    def queryset(self, request, queryset):
        if self.value() is not None:
            value = self.value()
            return queryset.filter(phase__competition__created_by__username=value)


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
    search_fields = ["id", "owner__username", "phase__competition__title", "task__name"]
    actions = [SubmissionsExport_as_csv]
    list_display = [
        "id",
        "owner",
        "task",
        "status",
        "is_public",
        "has_children",
        "is_soft_deleted",
    ]
    list_filter = [
        "is_public",
        "has_children",
        "is_soft_deleted",
        "status",
        CompetitionOrganizerFilter,
        QueueFilter,
    ]
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
    search_fields = ["id", "user__username", "competition"]


class PageExpansion(admin.ModelAdmin):
    raw_id_fields = ["competition"]
    list_display = ["id", "competition"]
    search_fields = ["id", "competition", "content"]


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
