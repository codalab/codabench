from django.contrib import admin

from .models import User, Organization


class UserAdmin(admin.ModelAdmin):
    # The following two lines are needed for Django-su:
    change_form_template = "admin/auth/user/change_form.html"
    change_list_template = "admin/auth/user/change_list.html"


admin.site.register(User, UserAdmin)
admin.site.register(Organization)


def su_login_callback(user):
    return user.is_superuser
