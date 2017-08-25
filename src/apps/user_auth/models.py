from django.utils import timezone

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def _create_user(self, uid, password, **extra_fields):
        """
        Creates and saves a User with the given id and password,
        :param id:
        :param password:
        :param extra_fields:
        :return:
        """
        if not uid:
            raise ValueError('The given uid must be set')
        user = self.model(uid=uid, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, uid, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(uid, password, **extra_fields)

    def create_superuser(self, uid, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuse=True.')
        return self._create_user(uid, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # Social needs the below setting. Username is not really set to UID.
    USERNAME_FIELD = 'uid'
    # Github user attributes.
    uid = models.CharField(max_length=30, unique=True, blank=True, null=True)
    login = models.CharField(max_length=50, blank=True, null=True)
    avatar_url = models.CharField(max_length=100, null=True, blank=True)
    url = models.CharField(max_length=100, null=True, blank=True)
    html_url = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    bio = models.CharField(max_length=300, null=True, blank=True)
    # Any User Attributes
    username = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=200, unique=True)
    # Utillity Attributes
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # Required
    objects = UserManager()

    def get_short_name(self):
        return self.name

    def get_full_name(self):
        return self.name
