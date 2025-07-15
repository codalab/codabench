from django.contrib import admin

from .models import User, DeletedUser, Organization, Membership


class UserAdmin(admin.ModelAdmin):
    # The following two lines are needed for Django-su:
    change_form_template = "admin/auth/user/change_form.html"
    change_list_template = "admin/auth/user/change_list.html"
    search_fields = ['username', 'email']
    list_filter = ['is_staff', 'is_superuser', 'is_deleted', 'is_bot']
    list_display = ['username', 'email', 'is_staff', 'is_superuser']


class DeletedUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'email', 'deleted_at')
    search_fields = ('username', 'email')
    list_filter = ('deleted_at',)


admin.site.register(User, UserAdmin)
admin.site.register(DeletedUser, DeletedUserAdmin)
admin.site.register(Organization)
admin.site.register(Membership)


def su_login_callback(user):
    return user.is_superuser
