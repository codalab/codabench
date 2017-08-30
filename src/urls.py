from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Our URLS
    url(r'', include('pages.urls', namespace='pages')),
    url(r'^registration/', include('user_auth.urls', namespace='user_auth')),

    # Third party
    url('^api/', include('api.urls')),
    url('^oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # Django built in
    url('^accounts/', include('django.contrib.auth.urls')),
    url('^admin/', include(admin.site.urls)),
    url('^social/', include('social_django.urls', namespace='social')),

    # TODO: these are in accounts! Get rid of them and reference accounts/login instead
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    # END TODO
    url(r'^admin/', include(admin.site.urls)),
]
