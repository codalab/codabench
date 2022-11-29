from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    # url(r'^signup', views.sign_up, name="signup"),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('user/<slug:username>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('user/<slug:username>/notifications/', views.UserNotificationEdit.as_view(), name="user_notifications"),
    path('user/<slug:username>/', views.UserDetailView.as_view(), name="user_profile"),
    path('organization/create/', views.OrganizationCreateView.as_view(), name='organization_create'),
    path('organization/accept_invite/', views.OrganizationInviteView.as_view(), name='organization_accept_invite'),
    path('organization/<int:pk>/edit/', views.OrganizationEditView.as_view(), name='organization_edit'),
    path('organization/<int:pk>/', views.OrganizationDetailView.as_view(), name="organization_profile"),
]
