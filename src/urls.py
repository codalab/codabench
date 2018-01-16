from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path

urlpatterns = [
    # Our URLS
    path('', include('pages.urls', namespace='pages')),
    path('competitions/', include('competitions.urls', namespace='competitions')),
    path('profiles/', include('profiles.urls', namespace='profiles')),

    # Third party
    path('api/', include('api.urls')),
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # Django built in
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('social/', include('social_django.urls', namespace='social')),
]
