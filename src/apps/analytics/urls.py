from django.urls import path

from . import views

app_name = "Analytics"

urlpatterns = [
    path('', views.AnalyticsView.as_view(), name="analytics"),
]
