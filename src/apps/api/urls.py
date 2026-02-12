from django.conf.urls import include
from django.urls import path


from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    analytics,
    competitions,
    datasets,
    profiles,
    leaderboards,
    submissions,
    tasks,
    queues,
    quota
)


router = SimpleRouter()
router.register('competitions', competitions.CompetitionViewSet)
router.register('phases', competitions.PhaseViewSet, 'phases')
router.register('submissions', submissions.SubmissionViewSet)
router.register('datasets', datasets.DataViewSet)
router.register('leaderboards', leaderboards.LeaderboardViewSet)
router.register('submission_scores', leaderboards.SubmissionScoreViewSet, 'submission_scores')
router.register('tasks', tasks.TaskViewSet)
router.register('participants', competitions.CompetitionParticipantViewSet, 'participants')
router.register('queues', queues.QueueViewSet, 'queues')
router.register('users', profiles.UserViewSet, 'users')
router.register('organizations', profiles.OrganizationViewSet, 'organizations')


urlpatterns = [
    path('my_profile/', profiles.GetMyProfile.as_view()),
    path('datasets/completed/<uuid:key>/', datasets.upload_completed),
    path('upload_submission_scores/<int:submission_pk>/', submissions.upload_submission_scores),
    path('can_make_submission/<phase_id>/', submissions.can_make_submission, name="can_make_submission"),
    path('user_lookup/', profiles.user_lookup),
    path('analytics/', analytics.AnalyticsView.as_view(), name='analytics_api'),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', obtain_auth_token),

    # User quota and cleanup
    path('user_quota_cleanup/', quota.user_quota_cleanup, name="user_quota_cleanup"),
    path('user_quota/', quota.user_quota, name="user_quota"),
    path('delete_unused_tasks/', quota.delete_unused_tasks, name="delete_unused_tasks"),
    path('delete_unused_datasets/', quota.delete_unused_datasets, name="delete_unused_datasets"),
    path('delete_unused_submissions/', quota.delete_unused_submissions, name="delete_unused_submissions"),
    path('delete_failed_submissions/', quota.delete_failed_submissions, name="delete_failed_submissions"),

    # User account
    path('delete_account/', profiles.delete_account, name="delete_account"),

    # Analytics
    path('analytics/storage_usage_history/', analytics.storage_usage_history, name='storage_usage_history'),
    path('analytics/competitions_usage/', analytics.competitions_usage, name='competitions_usage'),
    path('analytics/users_usage/', analytics.users_usage, name='users_usage'),
    path('analytics/delete_orphan_files/', analytics.delete_orphan_files, name="delete_orphan_files"),
    path('analytics/get_orphan_files/', analytics.get_orphan_files, name="get_orphan_files"),
    path('analytics/check_orphans_deletion_status/', analytics.check_orphans_deletion_status, name="check_orphans_deletion_status"),

    # API Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='schema-swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='schema-redoc'),

    # Include this at the end so our URLs above run first, like /datasets/completed/<pk>/ before /datasets/<pk>/
    path('', include(format_suffix_patterns(router.urls, allowed=['html', 'json', 'csv', 'zip']))),
]
