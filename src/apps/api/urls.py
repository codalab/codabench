from django.conf.urls import include
from django.urls import path
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import SimpleRouter

from .views import competitions, datasets, profiles, leaderboards


router = SimpleRouter()
router.register('competitions', competitions.CompetitionViewSet)
router.register('competition_status', competitions.CompetitionCreationTaskStatusViewSet)
router.register('phases', competitions.PhaseViewSet)
router.register('submissions', competitions.SubmissionViewSet)
router.register('datasets', datasets.DataViewSet)
router.register('data_groups', datasets.DataGroupViewSet)
router.register('leaderboards', leaderboards.LeaderboardViewSet)
# router.register(r'groups', GroupViewSet)
# router.register('query', SearchAPIView, base_name='Search')
# router.register('query', url('^query/', query), base_name='query')

urlpatterns = [
    # url('^query/', search.query),
    path('my_profile/', profiles.GetMyProfile.as_view()),
    path('datasets/completed/<uuid:key>/', datasets.upload_completed),
    path('datasets/create_dump/<int:competition_id>/', datasets.create_competition_dump),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('docs/', include_docs_urls(title='My API title')),

    # Include this at the end so our URLs above run first, like /datasets/completed/<pk>/ before /datasets/<pk>/
    path('', include(router.urls)),
]
