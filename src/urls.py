from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    # Our URLS
    path('', include('pages.urls', namespace='pages')),
    path('management/', include('management.urls', namespace='management')),
    path('competitions/', include('competitions.urls', namespace='competitions')),
    path('datasets/', include('datasets.urls', namespace='datasets')),
    path('profiles/', include('profiles.urls', namespace='profiles')),
    path('tasks/', include('tasks.urls', namespace='tasks')),

    # Third party
    path('api/', include('api.urls')),
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # Django built in
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('social/', include('social_django.urls', namespace='social')),
]


if settings.DEBUG:
    # Static files for local dev, so we don't have to collectstatic and such
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)

    # Django debug toolbar
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
