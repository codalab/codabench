from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    # url(r'^signup', views.sign_up, name="signup"),
    path('user/<slug:username>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('user/<slug:username>/', views.UserDetailView.as_view(), name="user_profile"),
    path('organization/create/', views.OrganizationCreateView.as_view(), name='organization_create'),
    # path('organization/<int:pk>/edit/', views.UserEditView.as_view(), name='organization_edit'),
    # path('organization/<int:pk>/', views.UserDetailView.as_view(), name="organization_profile"),
]
