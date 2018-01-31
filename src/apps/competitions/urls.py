from django.urls import path

from . import views

app_name = "competitions"

urlpatterns = [
    # path('', views.CompetitionList.as_view(), name="list"),
    path('', views.CompetitionManagement.as_view(), name="management"),
    path('form', views.CompetitionForm.as_view(), name="form"),
    path('edit/<int:pk>/', views.CompetitionForm.as_view(), name="edit"),
    path('detail/<int:pk>/', views.CompetitionDetail.as_view(), name="detail"),
]
