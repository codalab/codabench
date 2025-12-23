from django.contrib import admin

from .models import User, DeletedUser, Organization, Membership


class UserExpansion(admin.ModelAdmin):
    # The following two lines are needed for Django-su:
    change_form_template = "admin/auth/user/change_form.html"
    change_list_template = "admin/auth/user/change_list.html"
    search_fields = ["username", "email", "id"]
    list_filter = ["is_staff", "is_superuser", "is_deleted", "is_bot", "is_banned"]
    list_display = ["id", "username", "email", "is_staff", "is_superuser", "is_banned"]
    raw_id_fields = ["oidc_organization", "groups"]


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
