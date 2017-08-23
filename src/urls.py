from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views


urlpatterns = [
    url(r'', include('pages.urls', namespace='pages')),
    # url(r'^business/', include('businesses.urls', namespace='businesses')),

    # Third party
    url('^api/', include('api.urls')),
    url('', include('social_django.urls', namespace='social')),

    # Django built in
    url('^accounts/', include('django.contrib.auth.urls')),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^admin/', include(admin.site.urls)),
]
