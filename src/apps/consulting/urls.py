from django.urls import path

from consulting import views


app_name = 'consulting'

urlpatterns = [
    path('', views.ConsultingPublic.as_view(), name='public'),
    path('my-listing/', views.ConsultingMyListing.as_view(), name='my_listing'),
]
