from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'', include('pages.urls', namespace='pages')),
    # url(r'^business/', include('businesses.urls', namespace='businesses')),

    # Third party
    url('^api/', include('api.urls')),
    url('^oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # Django built in
    url('^accounts/', include('django.contrib.auth.urls')),
    url('^admin/', include(admin.site.urls)),
]
