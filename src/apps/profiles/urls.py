from django.conf.urls import url
from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    # url(r'^signup', views.sign_up, name="signup"),
    path('edit/<slug:username>/', views.UserDetail.as_view(), name='edit'),
    path(r'user_profile/<slug:username>/', views.user_profile, name="user_profile"),
]
