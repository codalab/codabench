from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url('', include('pages.urls', namespace='pages')),
    # url('r^search/', include('search.urls', namespace='search')),
    # url(r'^business/', include('businesses.urls', namespace='businesses')),

    # Third party
    url('^api/', include('api.urls')),

    # Django built in
    url('^accounts/', include('django.contrib.auth.urls')),
    url('^admin/', include(admin.site.urls)),
]
