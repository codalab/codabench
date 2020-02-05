from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, UserManager
from django.db import models
from django.utils.timezone import now
from chahub.models import ChaHubSaveMixin


PROFILE_DATA_BLACKLIST = [
    'password',
    'groups',
    'user_permissions'
]


class ChaHubUserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)

    def all_objects(self):
        return super().get_queryset()


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

    github_info = models.OneToOneField('GithubUserInfo', related_name='user', null=True, blank=True, on_delete=models.CASCADE)

    # Any User Attributes
    username = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=200, unique=True, null=True, blank=True)

    # Utility Attributes
    date_joined = models.DateTimeField(default=now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    rabbitmq_queue_limit = models.PositiveIntegerField(default=5, blank=True)
    rabbitmq_username = models.CharField(max_length=36, null=True, blank=True)
    rabbitmq_password = models.CharField(max_length=36, null=True, blank=True)

    # Required for social auth and such to create users
    objects = ChaHubUserManager()

    def get_short_name(self):
        return self.name

    def get_full_name(self):
        return self.name

    def __str__(self):
        return self.name if self.name else self.username

    @staticmethod
    def get_chahub_endpoint():
        return "profiles/"

    def get_whitelist(self):
        # all chahub data is ok to send
        pass

    def clean_private_data(self, data):
        # overriding this to filter out blacklist data from above, just to make _sure_ we don't send that info
        return {k: v for k, v in data.items() if k not in PROFILE_DATA_BLACKLIST}

    def get_chahub_data(self):
        data = {
            'email': self.email,
            'username': self.username,
            'remote_id': self.pk,
            'details': {
                "is_active": self.is_active,
                "last_login": self.last_login.isoformat() if self.last_login else None,
                "date_joined": self.date_joined.isoformat() if self.date_joined else None,
            }
        }
        return self.clean_private_data(data)

    def get_chahub_is_valid(self):
        # By default, always push
        return True


class GithubUserInfo(models.Model):
    # Required Info
    uid = models.CharField(max_length=30, unique=True)

    # Misc/Avatar/Profile
    login = models.CharField(max_length=100, null=True, blank=True)  # username
    avatar_url = models.URLField(max_length=100, null=True, blank=True)
    gravatar_id = models.CharField(max_length=100, null=True, blank=True)
    html_url = models.URLField(max_length=100, null=True, blank=True)  # Profile URL
    name = models.CharField(max_length=100, null=True, blank=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(max_length=2000, null=True, blank=True)
    location = models.CharField(max_length=120, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    # API Info
    node_id = models.CharField(unique=True, max_length=50, default='')
    url = models.URLField(max_length=100, null=True, blank=True)  # Base API URL
    followers_url = models.URLField(max_length=100, null=True, blank=True)
    following_url = models.URLField(max_length=100, null=True, blank=True)
    gists_url = models.URLField(max_length=100, null=True, blank=True)
    starred_url = models.URLField(max_length=100, null=True, blank=True)
    subscriptions_url = models.URLField(max_length=100, null=True, blank=True)
    organizations_url = models.URLField(max_length=100, null=True, blank=True)
    repos_url = models.URLField(max_length=100, null=True, blank=True)
    events_url = models.URLField(max_length=100, null=True, blank=True)
    received_events_url = models.URLField(max_length=100, null=True, blank=True)
