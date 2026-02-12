from django.urls import path, re_path
from . import views
from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    re_path(r'^signup', views.sign_up, name="signup"),
    path('resend_activation/', views.resend_activation, name='resend_activation'),
    path('login/', views.log_in, name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('user/<slug:username>/account/', views.UserAccountView.as_view(), name="user_account"),
    path('delete/<uidb64>/<token>', views.delete, name='delete'),
]
