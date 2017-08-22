from django.conf.urls import url, include
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from . import views


router = routers.DefaultRouter()
router.register(r'competitions', views.CompetitionViewSet)
# router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^docs/', get_swagger_view(title='Codalab'))
]
