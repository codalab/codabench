from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Our URLS
    url(r'', include('pages.urls', namespace='pages')),
    url(r'^registration/', include('user_auth.urls', namespace='user_auth')),

    # Third party
    url('^api/', include('api.urls')),
    url('^social/', include('social_django.urls', namespace='social')),

    # Django built in
    url('^accounts/', include('django.contrib.auth.urls', namespace='accounts')),
    url(r'^admin/', include(admin.site.urls)),
]
