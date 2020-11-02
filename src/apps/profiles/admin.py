from django.contrib import admin

from .models import User


class UserAdmin(admin.ModelAdmin):
    # The following two lines are needed:
    change_form_template = "admin/auth/user/change_form.html"
    change_list_template = "admin/auth/user/change_list.html"


admin.site.register(User, UserAdmin)
