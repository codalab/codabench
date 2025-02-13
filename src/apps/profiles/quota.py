import logging
from .models import User

logger = logging.getLogger()


def reset_all_users_quota_to_gb():
    """
    Converts user quota from bytes to GB if it's stored in bytes.
    Skips users whose quota is already in GB.
    """
    users = User.objects.all()
    for user in users:
        # If quota is in bytes (greater than 1 GB in bytes)
        if user.quota > 1000 * 1000 * 1000:
            user.quota = user.quota / 1e9  # Convert to GB
            user.save()
