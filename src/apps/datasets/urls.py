from django.urls import path

from . import views

app_name = "datasets"

urlpatterns = [
    # path('', views.CompetitionList.as_view(), name="list"),
    path('', views.DataManagement.as_view(), name="management"),
    path('public/', views.DatasetsPublic.as_view(), name="public"),
    path('create/', views.DatasetCreate.as_view(), name="create"),
    path('download/<str:key>/', views.download, name="download"),
]
