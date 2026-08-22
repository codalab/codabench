from django.urls import path

from external_competitions import views


app_name = 'external_competitions'

urlpatterns = [
    path('', views.ExternalCompetitionsPublic.as_view(), name='public'),
]
