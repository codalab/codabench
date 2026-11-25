from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import OrphanFileCandidate, OrphanFilesJob

from .orphan_files.storage import (
    get_allowed_prefixes,
    get_allowed_prefixes_by_bucket,
)
from .orphan_files.cleanup import filter_candidates_by_prefix


class OrphanFilePrefixFilter(admin.SimpleListFilter):

    title = "File type"
    parameter_name = "prefix"

    def lookups(self, request, model_admin):
        return [
            (prefix, prefix)
            for prefix in get_allowed_prefixes()
        ]

    def queryset(self, request, queryset):

        prefix = self.value()

        if prefix is None:
            return queryset

        if prefix not in get_allowed_prefixes():
            return queryset.none()

        return filter_candidates_by_prefix(
            queryset,
            prefix,
        )


@admin.register(OrphanFilesJob)
class OrphanFilesJobAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "task_id",
        "job_type",
        "status",
        "formatted_prefix",
        "grace_period_days",
        "source_scan",
        "created_at",
        "started_at",
        "completed_at",
        "heartbeat_at",
        "view_candidates",
    )

    list_filter = (
        "job_type",
        "status",
        "prefix",
        "created_at",
    )

    search_fields = (
        "task_id",
        "prefix",
        "error",
    )

    readonly_fields = (
        "task_id",
        "job_type",
        "status",
        "prefix",
        "grace_period_days",
        "source_scan",
        "created_at",
        "started_at",
        "completed_at",
        "heartbeat_at",
        "result",
        "error",
    )

    ordering = ("-created_at",)
    list_per_page = 50
    list_select_related = ("source_scan",)
    show_full_result_count = False

    @admin.display(description="Prefix", ordering="prefix")
    def formatted_prefix(self, obj):
        return obj.prefix or "All"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False

        if obj is not None:
            return obj.status not in (
                OrphanFilesJob.Status.PENDING,
                OrphanFilesJob.Status.STARTED,
                OrphanFilesJob.Status.PROGRESS,
            )

        return True

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
        "file_prefix",
        "key",
        "formatted_size",
        "status",
        "last_modified",
        "processed_at",
    )

    list_filter = (
        "status",
        "bucket",
        OrphanFilePrefixFilter,
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
        "file_prefix",
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

    @admin.display(description="Prefix")
    def file_prefix(self, obj):

        prefixes = get_allowed_prefixes_by_bucket().get(
            obj.bucket,
            (),
        )

        for prefix in prefixes:
            if obj.key.startswith(prefix):
                return prefix

        return "-"

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
        if not request.user.is_superuser:
            return False

        if obj is not None:
            return not OrphanFilesJob.objects.filter(
                status__in=[
                    OrphanFilesJob.Status.PENDING,
                    OrphanFilesJob.Status.STARTED,
                    OrphanFilesJob.Status.PROGRESS,
                ]
            ).exists()

        return True
