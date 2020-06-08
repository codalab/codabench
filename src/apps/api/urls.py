from django.conf.urls import include
from django.urls import path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.routers import SimpleRouter
from rest_framework.permissions import AllowAny

from api.views.competitions import front_page_competitions
from .views import analytics, competitions, datasets, profiles, leaderboards, submissions, tasks, queues, benchmarks


router = SimpleRouter()
router.register('competitions', competitions.CompetitionViewSet)
router.register('competition_status', competitions.CompetitionCreationTaskStatusViewSet)
router.register('phases', competitions.PhaseViewSet, 'phases')
router.register('submissions', submissions.SubmissionViewSet)
router.register('datasets', datasets.DataViewSet)
router.register('data_groups', datasets.DataGroupViewSet)
router.register('leaderboards', leaderboards.LeaderboardViewSet)
router.register('submission_scores', leaderboards.SubmissionScoreViewSet, 'submission_scores')
router.register('tasks', tasks.TaskViewSet)
router.register('participants', competitions.CompetitionParticipantViewSet, 'participants')
router.register('queues', queues.QueueViewSet, 'queues')
router.register('benchmarks', benchmarks.BenchmarkViewSet)
router.register('benchmarks_status', benchmarks.BenchmarkCreationTaskStatusViewSet)

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
    path('add_submission_to_leaderboard/<int:submission_pk>/', leaderboards.add_submission_to_leaderboard),
    path('datasets/create_dump/<int:competition_id>/', datasets.create_competition_dump),
    path('user_lookup/', profiles.user_lookup),
    path('analytics/', analytics.AnalyticsView.as_view(), name='analytics_api'),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # path('docs/', include_docs_urls(
    #     title='Codalab Competitions V2',
    #     permission_classes=(AllowAny,),
    # )),
    re_path(r'docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('can_make_submission/<phase_id>/', submissions.can_make_submission, name="can_make_submission"),
    # Include this at the end so our URLs above run first, like /datasets/completed/<pk>/ before /datasets/<pk>/
    path('', include(router.urls)),
    path('front_page_competitions/', front_page_competitions, name='front_page_competitions'),
]
