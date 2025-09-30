from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from ajax_select import urls as ajax_select_urls


urlpatterns = [
    # Our URLS
    path('', include('pages.urls', namespace='pages')),
    path('competitions/', include('competitions.urls', namespace='competitions')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('datasets/', include('datasets.urls', namespace='datasets')),
    path('profiles/', include('profiles.urls', namespace='profiles')),
    path('tasks/', include('tasks.urls', namespace='tasks')),
    path('queues/', include('queues.urls', namespace="queues")),
    path('forums/', include('forums.urls', namespace="forums")),

    # Third party
    path('api/', include('api.urls')),
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('su/', include('django_su.urls')),
    path('ajax_select/', include(ajax_select_urls)),

    # Django built in
    # path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('profiles.urls_accounts')),
    path('admin/', admin.site.urls),
    path('social/', include('social_django.urls', namespace='social')),
    path('oidc/', include('oidc_configurations.urls')),

]


if settings.DEBUG:
    # Static files for local dev, so we don't have to collectstatic and such
    urlpatterns += staticfiles_urlpatterns()

    # Django debug toolbar
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
