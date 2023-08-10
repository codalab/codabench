from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
            else:
                return None
        except ObjectDoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            return user
        except ObjectDoesNotExist:
            return None
