import json
import datetime

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, UserManager
from django.db import models
from django.forms import model_to_dict
from django.utils.timezone import now

from apps.chahub.models import ChaHubSaveMixin


PROFILE_DATA_BLACKLIST = [
    'password',
    'groups',
    'user_permissions'
]


class User(ChaHubSaveMixin, AbstractBaseUser, PermissionsMixin):
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

    # Utility Attributes
    date_joined = models.DateTimeField(default=now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Required for social auth and such to create users
    objects = UserManager()

    def get_short_name(self):
        return self.name

    def get_full_name(self):
        return self.name

    def __str__(self):
        return self.name if self.name else self.username

    @property
    def chahub_uid(self):
        associations = self.social_auth.filter(provider='chahub')
        if associations.count() > 0:
            return associations.first().uid
        return None

    def get_chahub_endpoint(self):
        return "profiles/"

    def clean_chahub_data(self, temp_data):
        data = temp_data
        for key in list(data):
            if key == 'details':
                data['details'] = self.clean_chahub_data(data['details'])
            if not data[key] or data[key] == '':
                data.pop(key, None)
            if key in PROFILE_DATA_BLACKLIST:
                data.pop(key, None)
            if isinstance(data.get(key), datetime.datetime):
                data[key] = data[key].isoformat()
        return data

    def get_chahub_data(self):
        data = {
            'email': self.email,
            'username': self.username,
            'remote_id': self.pk,
            'details': model_to_dict(self),
        }
        chahub_id = self.chahub_uid
        if chahub_id:
            data['user'] = chahub_id
        data = self.clean_chahub_data(data)
        return [data]

    def get_chahub_is_valid(self):
        # By default, always push
        return True
