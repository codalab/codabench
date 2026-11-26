from django.urls import path

from papers.views import HallOfPapersView

app_name = 'papers'

urlpatterns = [
    path('', HallOfPapersView.as_view(), name='list'),
]
