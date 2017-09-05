from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, UserManager
from django.db import models


class User(AbstractBaseUser, PermissionsMixin):
    # Social needs the below setting. Username is not really set to UID.
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    # Github user attributes.
    github_uid = models.CharField(max_length=30, unique=True, blank=True, null=True)
    avatar_url = models.CharField(max_length=100, null=True, blank=True)
    url = models.CharField(max_length=100, null=True, blank=True)
    html_url = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    bio = models.CharField(max_length=300, null=True, blank=True)

    # Any User Attributes
    username = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=200, unique=True, null=True, blank=True)

    # Utillity Attributes
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Required for social auth and such to create users
    objects = UserManager()

    def get_short_name(self):
        return self.name

    def get_full_name(self):
        return self.name
