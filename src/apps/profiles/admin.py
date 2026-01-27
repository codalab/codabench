from django.contrib import admin
from .models import User, DeletedUser, Organization, Membership
from django.utils.translation import gettext_lazy as _
import json
import csv
from django.http import HttpResponse


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


class QuotaFilter(InputFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("≥ Quota (Greater than or Equal to)")
    # Parameter for the filter that will be used in the URL query.
    parameter_name = "quota_gte"

    def queryset(self, request, queryset):
        if self.value() is not None:
            value = self.value()
            return queryset.filter(quota__gte=value)


@admin.display(description="Export as CSV")
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="submissions.csv"'},
    )
    writer = csv.writer(response)
    writer.writerow(["ID", "Username", "Active", "Date_Joined"])
    for obj in queryset:
        writer.writerow(
            [
                obj.id,
                obj.username,
                obj.is_active,
                obj.date_joined,
            ]
        )
    return response


# This will export the email of all the selected competition creators, removing duplications and banned users
@admin.display(description="Export as JSON")
def export_as_json(modeladmin, request, queryset):
    email_list = {}
    for obj in queryset:
        email_list.update({obj.username: obj.email})
    return HttpResponse(json.dumps(email_list), content_type="application/json")


class UserExpansion(admin.ModelAdmin):
    # The following two lines are needed for Django-su:
    change_form_template = "admin/auth/user/change_form.html"
    change_list_template = "admin/auth/user/change_list.html"
    search_fields = ["id", "username", "email"]
    list_filter = [
        "is_staff",
        "is_superuser",
        "is_deleted",
        "is_bot",
        "is_banned",
        QuotaFilter,
    ]
    list_display = [
        "id",
        "username",
        "email",
        "quota",
        "is_staff",
        "is_superuser",
        "is_banned",
    ]
    list_display_links = ["id", "username"]
    raw_id_fields = ["oidc_organization", "groups"]
    actions = [export_as_csv, export_as_json]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    ("username", "slug", "email"),
                    "password",
                    "groups",
                    "user_permissions",
                    "date_joined",
                    "last_login",
                    "quota",
                ]
            },
        ),
        (
            "Checkboxes",
            {
                "fields": [
                    ("is_active", "is_bot"),
                    (
                        "organizer_direct_message_updates",
                        "allow_forum_notifications",
                        "allow_organization_invite_emails",
                    ),
                    ("is_superuser", "is_staff"),
                    "is_deleted",
                    "is_banned",
                ]
            },
        ),
        (
            "Extra Information",
            {
                "classes": ["collapse"],
                "fields": [
                    "display_name",
                    "first_name",
                    "last_name",
                    "title",
                    "location",
                    "biography",
                    "personal_url",
                    "linkedin_url",
                    "twitter_url",
                    "github_url",
                    "github_uid",
                    "avatar_url",
                    "url",
                    "html_url",
                    "name",
                    "company",
                    "bio",
                    "github_info",
                ],
            },
        ),
        (
            "OIDC",
            {
                "classes": ["collapse"],
                "fields": ["is_created_using_oidc", "oidc_organization"],
            },
        ),
        (
            "RabbitMQ",
            {
                "classes": ["collapse"],
                "fields": [
                    "rabbitmq_queue_limit",
                    "rabbitmq_username",
                    "rabbitmq_password",
                ],
            },
        ),
        ("Files", {"classes": ["collapse"], "fields": ["photo"]}),
    ]


class DeletedUserExpansion(admin.ModelAdmin):
    list_display = ("user_id", "username", "email", "deleted_at")
    search_fields = ("id", "username", "email")
    list_filter = ("deleted_at",)


class MembershipExpansion(admin.ModelAdmin):
    raw_id_fields = ["organization", "user"]
    list_display = ["id", "organization", "user", "group"]
    search_fields = ["id", "user__username", "token"]


class OrganizationExpansion(admin.ModelAdmin):
    raw_id_fields = ["user_record"]
    list_display = ["id", "name", "email", "description"]
    search_fields = ["name", "email", "description"]


admin.site.register(User, UserExpansion)
admin.site.register(DeletedUser, DeletedUserExpansion)
admin.site.register(Organization, OrganizationExpansion)
admin.site.register(Membership, MembershipExpansion)


def su_login_callback(user):
    return user.is_superuser
