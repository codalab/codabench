from django.contrib import admin

from .models import User, DeletedUser, Organization, Membership


class UserExpansion(admin.ModelAdmin):
    # The following two lines are needed for Django-su:
    change_form_template = "admin/auth/user/change_form.html"
    change_list_template = "admin/auth/user/change_list.html"
    search_fields = ['username', 'email']
    list_filter = ['is_staff', 'is_superuser', 'is_deleted', 'is_bot', 'is_banned']
    list_display = ['username', 'email', 'is_staff', 'is_superuser', 'is_banned']


class DeletedUserExpansion(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'email', 'deleted_at')
    search_fields = ('username', 'email')
    list_filter = ('deleted_at',)


admin.site.register(User, UserExpansion)
admin.site.register(DeletedUser, DeletedUserExpansion)
admin.site.register(Organization)
admin.site.register(Membership)


def su_login_callback(user):
    return user.is_superuser
