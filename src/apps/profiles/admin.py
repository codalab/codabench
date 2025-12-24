from django.contrib import admin

from .models import User, DeletedUser, Organization, Membership


class UserExpansion(admin.ModelAdmin):
    # The following two lines are needed for Django-su:
    change_form_template = "admin/auth/user/change_form.html"
    change_list_template = "admin/auth/user/change_list.html"
    search_fields = ["username", "email", "id"]
    list_filter = ["is_staff", "is_superuser", "is_deleted", "is_bot", "is_banned"]
    list_display = ["id", "username", "email", "is_staff", "is_superuser", "is_banned"]
    list_display_links = ["id", "username"]
    raw_id_fields = ["oidc_organization", "groups"]
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
            "Advanced Options",
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
    search_fields = ("username", "email")
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
