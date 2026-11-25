from django.contrib import admin

from .models import OrphanFileCandidate, OrphanFilesJob
from django.urls import reverse
from django.utils.html import format_html


@admin.register(OrphanFilesJob)
class OrphanFilesJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "task_id",
        "job_type",
        "status",
        "grace_period_days",
        "source_scan",
        "created_at",
        "started_at",
        "completed_at",
        "heartbeat_at",
        "view_candidates"
    )

    list_filter = (
        "job_type",
        "status",
        "created_at"
    )

    search_fields = (
        "task_id",
        "error"
    )

    readonly_fields = (
        "task_id",
        "job_type",
        "status",
        "grace_period_days",
        "source_scan",
        "created_at",
        "started_at",
        "completed_at",
        "heartbeat_at",
        "result",
        "error"
    )

    ordering = ("-created_at",)
    list_per_page = 50
    list_select_related = ("source_scan",)
    show_full_result_count = False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Candidates")
    def view_candidates(self, obj):
        if obj.job_type != OrphanFilesJob.JobType.SCAN:
            return "-"

        url = reverse(
            "admin:analytics_orphanfilecandidate_changelist"
        )

        return format_html(
            '<a href="{}?scan__id__exact={}">View candidates</a>',
            url,
            obj.pk,
        )


@admin.register(OrphanFileCandidate)
class OrphanFileCandidateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "scan_id",
        "bucket",
        "key",
        "formatted_size",
        "status",
        "last_modified",
        "processed_at",
    )

    list_filter = (
        "status",
        "bucket",
        "last_modified",
    )

    search_fields = (
        "key",
        "bucket",
        "scan__task_id",
    )

    readonly_fields = (
        "scan",
        "bucket",
        "key",
        "size",
        "etag",
        "status",
        "last_modified",
        "processed_at",
        "error",
    )

    ordering = ("-id",)
    list_per_page = 100
    list_select_related = ("scan",)
    show_full_result_count = False

    @admin.display(description="Size", ordering="size")
    def formatted_size(self, obj):
        size = float(obj.size)

        for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
            if size < 1024 or unit == "TiB":
                return f"{size:.2f} {unit}"

            size /= 1024

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
