import logging

import requests
from celery import task
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from apps.chahub.utils import send_to_chahub, ChahubException
from chahub.models import ChaHubSaveMixin
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


@task(queue='site-worker')
def do_chahub_retries(limit=None):
    if not settings.CHAHUB_API_URL:
        return

    logger.info("Checking whether ChaHub is online before sending retries")
    try:
        response = requests.get(settings.CHAHUB_API_URL)
        if response.status_code != 200:
            return
    except requests.exceptions.RequestException:
        # This base exception works for HTTP errors, Connection errors, etc.
        return

    logger.info("ChaHub is online, checking for objects needing to be re-sent to ChaHub")
    chahub_models = ChaHubSaveMixin.__subclasses__()
    for model in chahub_models:
        needs_retry = model.objects.filter(chahub_needs_retry=True)

        if limit:
            needs_retry = needs_retry[:limit]

        for instance in needs_retry:
            # Saving forces chahub update
            instance.save()
