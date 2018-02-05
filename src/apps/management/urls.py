from django.urls import path

from . import views

app_name = "management"

urlpatterns = [
    path('submissions', views.SubmissionsView.as_view(), name="submissions"),
]
