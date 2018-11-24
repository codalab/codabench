from django.conf.urls import include, url
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.routers import SimpleRouter
from rest_framework.permissions import AllowAny

from .views import competitions, datasets, profiles, leaderboards, submissions


router = SimpleRouter()
router.register('competitions', competitions.CompetitionViewSet)
router.register('competition_status', competitions.CompetitionCreationTaskStatusViewSet)
router.register('phases', competitions.PhaseViewSet)
router.register('submissions', submissions.SubmissionViewSet)
router.register('datasets', datasets.DataViewSet)
router.register('data_groups', datasets.DataGroupViewSet)
router.register('leaderboards', leaderboards.LeaderboardViewSet)

schema_view = get_schema_view(
   openapi.Info(
      title="Codalab Competitions API",
      default_version='v1',
   ),
   validators=['flex', 'ssv'],
   public=True,
   permission_classes=(AllowAny,),
)

urlpatterns = [
    # url('^query/', search.query),
    path('my_profile/', profiles.GetMyProfile.as_view()),
    path('datasets/completed/<uuid:key>/', datasets.upload_completed),
    path('upload_submission_scores/<int:submission_pk>/', submissions.upload_submission_scores),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # path('docs/', include_docs_urls(
    #     title='Codalab Competitions V2',
    #     permission_classes=(AllowAny,),
    # )),
    url(r'swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Include this at the end so our URLs above run first, like /datasets/completed/<pk>/ before /datasets/<pk>/
    path('', include(router.urls)),
]
