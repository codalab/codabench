from django.urls import path

from . import views

app_name = "competitions"

urlpatterns = [
    # path('', views.CompetitionList.as_view(), name="list"),
    path('management', views.CompetitionManagement.as_view(), name="management"),
]
