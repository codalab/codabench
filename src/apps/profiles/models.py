from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, UserManager
from django.db import models
from django.utils.timezone import now
from chahub.models import ChaHubSaveMixin
from django.utils.text import slugify
from utils.data import PathWrapper
from django.urls import reverse


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
    slug = models.SlugField(max_length=50, default='', unique=True)
    photo = models.ImageField(upload_to=PathWrapper('profile_photos'), null=True, blank=True)
    email = models.EmailField(max_length=200, unique=True, null=True, blank=True)
    display_name = models.CharField(max_length=50, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=200, unique=False, null=True, blank=True)
    last_name = models.CharField(max_length=200, unique=False, null=True, blank=True)
    title = models.CharField(max_length=200, unique=False, null=True, blank=True)
    location = models.CharField(max_length=250, unique=False, null=True, blank=True)
    biography = models.CharField(max_length=4096, unique=False, null=True, blank=True)
    personal_url = models.URLField(unique=False, null=True, blank=True)
    linkedin_url = models.URLField(unique=False, null=True, blank=True)
    twitter_url = models.URLField(unique=False, null=True, blank=True)
    github_url = models.URLField(unique=False, null=True, blank=True)

    # Utility Attributes
    date_joined = models.DateTimeField(default=now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Notifications
    organizer_direct_message_updates = models.BooleanField(default=True)
    allow_forum_notifications = models.BooleanField(default=True)

    # Queues
    rabbitmq_queue_limit = models.PositiveIntegerField(default=5, blank=True)
    rabbitmq_username = models.CharField(max_length=36, null=True, blank=True)
    rabbitmq_password = models.CharField(max_length=36, null=True, blank=True)

    # Robot submissions
    is_bot = models.BooleanField(default=False)

    # Required for social auth and such to create users
    objects = ChaHubUserManager()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.username, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_short_name(self):
        return self.name

    def get_full_name(self):
        return self.name

    def __str__(self):
        return f'Username-{self.username} | Name-{self.name}'

    @property
    def slug_url(self):
        return reverse('profiles:user_profile', args=[self.slug])

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


class Organization(models.Model):
    users = models.ManyToManyField(User, related_name='organizations', through='Membership')

    # slug = models.SlugField(max_length=50, default='', unique=True)
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)
    photo = models.ImageField(upload_to=PathWrapper('organization_photos'), null=True, blank=True)
    email = models.EmailField(max_length=200, unique=True, null=False, blank=False)
    location = models.CharField(max_length=250, unique=False, null=True, blank=True)
    description = models.CharField(max_length=4096, unique=False, null=True, blank=True)
    website_url = models.URLField(unique=False, null=True, blank=True)
    linkedin_url = models.URLField(unique=False, null=True, blank=True)
    twitter_url = models.URLField(unique=False, null=True, blank=True)
    github_url = models.URLField(unique=False, null=True, blank=True)

    # Utility Attributes
    date_created = models.DateTimeField(default=now)

    def __str__(self):
        return f'{self.name}({self.email})'


class Membership(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_joined = models.DateField(default=now)

    # Permissions
    OWNER = 'OWNER'
    MANAGER = 'MANAGER'
    PARTICIPANT = 'PARTICIPANT'
    MEMBER = 'MEMBER'
    PERMISSION_GROUPS = ((OWNER, 'Owner'), (MANAGER, 'Manager'), (PARTICIPANT, 'Participant'), (MEMBER, 'Member'))
    group = models.TextField(choices=PERMISSION_GROUPS, default=MEMBER, null=False, blank=False)
