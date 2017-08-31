from django.conf.urls import url, include
from rest_framework.routers import SimpleRouter
from rest_framework_swagger.views import get_swagger_view

from .views import competitions, data, profiles, search

# from .views.search import query


router = SimpleRouter()
router.register('competitions', competitions.CompetitionViewSet)
router.register('phases', competitions.PhaseViewSet)
router.register('submissions', competitions.SubmissionViewSet)
router.register('data', data.DataViewSet)
router.register('data_groups', data.DataGroupViewSet)
# router.register(r'groups', GroupViewSet)
# router.register('query', SearchAPIView, base_name='Search')
# router.register('query', url('^query/', query), base_name='query')

urlpatterns = [
    url('^', include(router.urls)),
    url('^query/', search.query),
    url('^my_profile/', profiles.GetMyProfile.as_view()),

    url('^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url('^docs/', get_swagger_view(title='Codalab'))
]
