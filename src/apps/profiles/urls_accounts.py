from django.conf.urls import url
from django.urls import path
from . import views
# from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    url(r'^signup', views.sign_up, name="signup"),
    # url(r'^user_profile', views.user_profile, name="user_profile"),
    # path('login/', auth_views.LoginView.as_view(extra_context=extra_context), name='login'),
    path('login/', views.LoginView.as_view(), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
