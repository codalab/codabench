from django.urls import re_path

from . import views

app_name = "forums"

urlpatterns = [
    re_path(r'^pin/(?P<thread_pk>\d+)/$', views.pin_thread, name='forum_thread_pin'),

    re_path(r'^(?P<forum_pk>\d+)/$', views.ForumDetailView.as_view(), name='forum_detail'),
    re_path(r'^(?P<forum_pk>\d+)/new_thread/$', views.CreateThreadView.as_view(), name='forum_new_thread'),
    re_path(r'^(?P<forum_pk>\d+)/(?P<thread_pk>\d+)/$', views.ThreadDetailView.as_view(), name='forum_thread_detail'),
    re_path(r'^(?P<forum_pk>\d+)/(?P<thread_pk>\d+)/new_post/$', views.CreatePostView.as_view(), name='forum_new_post'),
    re_path(r'^(?P<forum_pk>\d+)/(?P<thread_pk>\d+)/delete/$', views.DeleteThreadView.as_view(), name='forum_delete_thread'),
    re_path(r'^(?P<forum_pk>\d+)/(?P<thread_pk>\d+)/delete/(?P<post_pk>\d+)/$', views.DeletePostView.as_view(), name='forum_delete_post'),
]
