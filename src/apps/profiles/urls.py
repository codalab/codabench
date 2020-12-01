from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    # url(r'^signup', views.sign_up, name="signup"),
    path('<slug:username>/edit/', views.UserEditView.as_view(), name='edit'),
    path('<slug:username>/', views.UserDetailView.as_view(), name="user_profile"),
]
