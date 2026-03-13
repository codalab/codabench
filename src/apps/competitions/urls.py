from django.urls import path

from . import views

app_name = "competitions"

urlpatterns = [
    # path('', views.CompetitionList.as_view(), name="list"),
    path('', views.CompetitionManagement.as_view(), name="management"),
    path('<int:pk>/', views.CompetitionDetail.as_view(), name="detail"),
    path('create/', views.CompetitionCreateForm.as_view(), name="create"),
    path('edit/<int:pk>/', views.CompetitionUpdateForm.as_view(), name="edit"),
    path('upload/', views.CompetitionUpload.as_view(), name="upload"),
    path('public/', views.CompetitionPublic.as_view(), name="public"),
    path('<int:pk>/detailed_results/<int:submission_id>/', views.CompetitionDetailedResults.as_view(), name="detailed_results"),

    #   Groups
    path('<int:pk>/groups/create/', views.competition_create_group, name='competition_create_group'),
    path('<int:pk>/groups/<int:group_id>/update/', views.competition_update_group),
    path('<int:pk>/groups/<int:group_id>/delete/', views.competition_delete_group),

]
