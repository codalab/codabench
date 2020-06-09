from django.urls import path

from . import views

app_name = "benchmarks"

urlpatterns = [
    path('', views.BenchmarkManagement.as_view(), name="management"),
    path('<int:pk>/', views.BenchmarkDetail.as_view(), name="detail"),
    path('create/', views.BenchmarkForm.as_view(), name="create"),
    path('edit/<int:pk>/', views.BenchmarkForm.as_view(), name="edit"),
    path('upload/', views.BenchmarkUpload.as_view(), name="upload"),
]
