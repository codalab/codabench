# oidc_configurations/urls.py
from django.urls import path
from .views import organization_oidc_login, oidc_complete

app_name = 'oidc_configurations'

urlpatterns = [
    path('organization_oidc_login/', organization_oidc_login, name='organization_oidc_login'),
    path('complete/<int:auth_organization_id>/', oidc_complete, name='oidc_complete'),
]
