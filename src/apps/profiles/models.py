import uuid

from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, UserManager
from django.db import models
from django.utils.timezone import now
from django.utils.text import slugify
from utils.data import PathWrapper
from django.urls import reverse
from django.conf import settings
from django.db.models import (
    Sum,
    F,
    Case,
    Value,
    When,
    DecimalField,
)
from oidc_configurations.models import Auth_Organization

PROFILE_DATA_BLACKLIST = [
    'password',
    'groups',
    'user_permissions'
]


class CodabenchUserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter()

    def all_objects(self):
        return super().get_queryset()


class DeletedUser(models.Model):
    user_id = models.IntegerField(null=True, blank=True)  # Store the same ID as in the User table
    username = models.CharField(max_length=255)
    email = models.EmailField()
    deleted_at = models.DateTimeField(auto_now_add=True)  # Automatically sets to current time when the record is created

    def __str__(self):
        return f"{self.username} ({self.email})"


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

    github_info = models.OneToOneField('GithubUserInfo', related_name='user', null=True, blank=True,
                                       on_delete=models.CASCADE)

    # Any User Attributes
    username = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, default='', unique=True)
    photo = models.ImageField(upload_to=PathWrapper('profile_photos'), null=True, blank=True)
    email = models.EmailField(max_length=200, unique=True, null=True, blank=True)
    display_name = models.CharField(max_length=50, null=True, blank=True)
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
    quota = models.BigIntegerField(default=settings.DEFAULT_USER_QUOTA, null=False, help_text="Size in GB")

    # Fields for OIDC authentication
    is_created_using_oidc = models.BooleanField(default=False)
    oidc_organization = models.ForeignKey(Auth_Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name="authorized_users")

    # Notifications
    organizer_direct_message_updates = models.BooleanField(default=True)
    allow_forum_notifications = models.BooleanField(default=True)
    allow_organization_invite_emails = models.BooleanField(default=True)

    # Queues
    rabbitmq_queue_limit = models.PositiveIntegerField(default=5, blank=True)
    rabbitmq_username = models.CharField(max_length=36, null=True, blank=True)
    rabbitmq_password = models.CharField(max_length=36, null=True, blank=True)

    # Robot submissions
    is_bot = models.BooleanField(default=False)

    # Required for social auth and such to create users
    objects = CodabenchUserManager()

    # Soft deletion
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Ban
    is_banned = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.username, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_short_name(self):
        return self.name

    def get_full_name(self):
        return self.name

    def __str__(self):
        return self.username

    @property
    def slug_url(self):
        return reverse('profiles:user_profile', args=[self.slug])

    def get_used_storage_space(self, binary=False):
        """
        Function to calculate storage used by a user
        Returns in bytes
        """

        from datasets.models import Data
        from competitions.models import Submission, SubmissionDetails

        storage_used = 0

        # Datasets
        users_datasets = Data.objects.filter(
            created_by_id=self.id, file_size__gt=0, file_size__isnull=False
        ).aggregate(Sum("file_size"))["file_size__sum"]

        storage_used += users_datasets if users_datasets else 0

        # Submissions
        users_submissions = Submission.objects.filter(owner_id=self.id).aggregate(
            size=Sum(
                Case(
                    When(
                        prediction_result_file_size__gt=0,
                        then=F("prediction_result_file_size"),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                ) +
                Case(
                    When(
                        scoring_result_file_size__gt=0,
                        then=F("scoring_result_file_size"),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                ) +
                Case(
                    When(
                        detailed_result_file_size__gt=0,
                        then=F("detailed_result_file_size"),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )

        storage_used += users_submissions["size"] if users_submissions["size"] else 0

        # Submissions details
        users_submissions_details = SubmissionDetails.objects.filter(
            submission__owner_id=self.id, file_size__gt=0, file_size__isnull=False
        ).aggregate(Sum("file_size"))["file_size__sum"]

        storage_used += users_submissions_details if users_submissions_details else 0

        return storage_used

    def delete(self, *args, **kwargs):
        """Soft delete the user and anonymize personal data."""
        from .views import send_user_deletion_notice_to_admin, send_user_deletion_confirmed
        from .models import DeletedUser

        # Send a notice to admins
        send_user_deletion_notice_to_admin(self)

        # Mark the user as deleted
        self.is_deleted = True
        self.deleted_at = now()
        self.is_active = False

        # Anonymize or removed personal data
        user_email = self.email  # keep track of the email for the end of the procedure

        # Store the deleted user's data in the DeletedUser table
        DeletedUser.objects.create(
            user_id=self.id,
            username=self.username,
            email=self.email
        )

        # Github related
        self.github_uid = None
        self.avatar_url = None
        self.url = None
        self.html_url = None
        self.name = None
        self.company = None
        self.bio = None
        if self.github_info:
            self.github_info.login = None
            self.github_info.avatar_url = None
            self.github_info.gravatar_id = None
            self.github_info.html_url = None
            self.github_info.name = None
            self.github_info.company = None
            self.github_info.bio = None
            self.github_info.location = None

        # Any user attribute
        self.username = f"deleted_user_{self.id}"
        self.slug = f"deleted_slug_{self.id}"
        self.photo = None
        self.email = None
        self.display_name = None
        self.first_name = None
        self.last_name = None
        self.title = None
        self.location = None
        self.biography = None
        self.personal_url = None
        self.linkedin_url = None
        self.twitter_url = None
        self.github_url = None

        # Queues
        self.rabbitmq_username = None
        self.rabbitmq_password = None

        # Save the changes
        self.save()

        # Send a confirmation email notice to the removed user
        send_user_deletion_confirmed(user_email)

    def restore(self, *args, **kwargs):
        """Restore a soft-deleted user. Note that personal data remains anonymized."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


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
    user_record = models.ManyToManyField(User)

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

    @property
    def url(self):
        return reverse('profiles:organization_profile', args=[self.id])


class Membership(models.Model):
    # Permissions
    OWNER = 'OWNER'
    MANAGER = 'MANAGER'
    PARTICIPANT = 'PARTICIPANT'
    MEMBER = 'MEMBER'
    INVITED = 'INVITED'
    PERMISSIONS = (
        (OWNER, 'Owner'),
        (MANAGER, 'Manager'),
        (PARTICIPANT, 'Participant'),
        (MEMBER, 'Member'),
        (INVITED, 'Invited'),
    )
    # Groups
    EDITORS_GROUP = [OWNER, MANAGER]
    PARTICIPANT_GROUP = EDITORS_GROUP + [PARTICIPANT]
    SETTABLE_PERMISSIONS = [MANAGER, PARTICIPANT, MEMBER]
    ALL_GROUP = EDITORS_GROUP + [PARTICIPANT, MEMBER]

    group = models.TextField(choices=PERMISSIONS, default=INVITED, null=False, blank=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(default=now)
    token = models.UUIDField(default=uuid.uuid4, unique=True)

    class Meta:
        ordering = ["date_joined"]
