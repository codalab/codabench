from django.conf.urls import url, include
from rest_framework.routers import SimpleRouter
# from rest_framework_swagger.views import get_swagger_view

from . import views

from .views.search import query


router = SimpleRouter()
router.register('competitions', views.CompetitionViewSet)
router.register('phases', views.PhaseViewSet)
router.register('submissions', views.SubmissionViewSet)
router.register('data', views.DataViewSet)
router.register('data_groups', views.DataGroupViewSet)
# router.register(r'groups', views.GroupViewSet)
# router.register('query', views.SearchAPIView, base_name='Search')
# router.register('query', url('^query/', query), base_name='query')

urlpatterns = [
    url('^', include(router.urls)),
    url('^query/', query),

    url('^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # url('^docs/', get_swagger_view(title='Codalab'))
    url(r'^docs/', include('rest_framework_docs.urls')),
]
