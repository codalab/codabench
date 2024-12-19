from django.contrib import admin

from .models import User, Organization, Membership


class UserAdmin(admin.ModelAdmin):
    # The following two lines are needed for Django-su:
    change_form_template = "admin/auth/user/change_form.html"
    change_list_template = "admin/auth/user/change_list.html"
    search_fields = ['username', 'email']
    list_filter = ["is_staff", "is_superuser", "deleted", "is_bot"]
    list_display = ['username', 'email', "is_staff", "is_superuser"]


admin.site.register(User, UserAdmin)
admin.site.register(Organization)
admin.site.register(Membership)


def su_login_callback(user):
    return user.is_superuser
