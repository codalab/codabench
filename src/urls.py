from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    # Our URLS
    url('', include('pages.urls', namespace='pages')),
    url('^profiles/', include('profiles.urls', namespace='profiles')),

    # Third party
    url('^api/', include('api.urls')),
    url('^oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # Django built in
    url('^accounts/', include('django.contrib.auth.urls', namespace='accounts')),
    url('^admin/', include(admin.site.urls)),
    url('^social/', include('social_django.urls', namespace='social')),
]
