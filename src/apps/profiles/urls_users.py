from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    # My profile: the profile of the logged-in user. Why no username: it always shows the logged-in user.
    path('profile/', views.MyProfileView.as_view(), name="my_profile"),
    # The public profile of any user, for example /user/jane/
    path('user/<slug:username>/', views.PublicProfileView.as_view(), name="profile"),
]
