import logging
from celery import task
from datetime import timedelta
from django.utils import timezone
from apps.chahub.utils import send_to_chahub, ChahubException
from profiles.models import User

logger = logging.getLogger(__name__)


@task
def send_users_to_chahub():
    all_users = User.objects.all()
    user_data_list = []
    for user in all_users:
        user_data_list.append(user.get_chahub_data())
    try:
        logger.info("Sending profile data to Chahub")
        resp = send_to_chahub('profiles/', user_data_list, update=False)
        logger.info(f"Response Status Code: {resp.status_code}")
    # TODO: Will this catch timeouts and errors from our code? We should bubble up errors from send_to_chahub nicely.
    except ChahubException:
        logger.info("There was a problem reaching Chahub, it is currently offline. Re-trying in 5 minutes.")
        send_users_to_chahub.apply_async(eta=timezone.now() + timedelta(minutes=5))
