from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'test', views.CompetitionListTestView.as_view()),
]
