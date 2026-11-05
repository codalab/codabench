from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "settings"

# These pages always show the logged-in user, so the urls need no username
urlpatterns = [
    path('', RedirectView.as_view(pattern_name='settings:notifications'), name="home"),
    path('notifications/', views.NotificationSettingsView.as_view(), name="notifications"),
    path('change-password/', views.ChangePasswordSettingsView.as_view(), name="change_password"),
    path('delete-account/', views.DeleteAccountSettingsView.as_view(), name="delete_account"),
]
