import json
import logging

import requests
from django.utils import timezone

from celery_config import app
from django.apps import apps
from django.conf import settings
from apps.chahub.utils import ChahubException

logger = logging.getLogger(__name__)


def _send(endpoint, data):
    url = f"{settings.CHAHUB_API_URL}{endpoint}"
    headers = {
        'Content-type': 'application/json',
        'X-CHAHUB-API-KEY': settings.CHAHUB_API_KEY,
    }
    logger.info(f"ChaHub :: Sending to ChaHub ({url}) the following data: \n{data}")
    return requests.post(url=url, data=json.dumps(data), headers=headers)


def get_obj(app_label, pk, include_deleted=False):
    Model = apps.get_model(app_label)

    try:
        if include_deleted:
            obj = Model.objects.all_objects().get(pk=pk)
        else:
            obj = Model.objects.get(pk=pk)
    except Model.DoesNotExist:
        raise ChahubException(f"Could not find {app_label} with pk: {pk}")
    return obj


@app.task(queue='site-worker')
def send_to_chahub(app_label, pk, data, data_hash):
    """
    Does a post request to the specified API endpoint on chahub with the inputted data.
    """
    if not settings.CHAHUB_API_URL:
        raise ChahubException("CHAHUB_API_URL env var required to send to Chahub")
    if not settings.CHAHUB_API_KEY:
        raise ChahubException("No ChaHub API Key provided")

    obj = get_obj(app_label, pk)

    try:
        resp = _send(obj.get_chahub_endpoint(), data)
    except requests.exceptions.RequestException:
        resp = None

    if resp and resp.status_code in (200, 201):
        logger.info(f"ChaHub :: Received response {resp.status_code} {resp.content}")
        obj.chahub_timestamp = timezone.now()
        obj.chahub_data_hash = data_hash
        obj.chahub_needs_retry = False
    else:
        status = getattr(resp, 'status_code', 'N/A')
        body = getattr(resp, 'content', 'N/A')
        logger.info(f"ChaHub :: Error sending to chahub, status={status}, body={body}")
        obj.chahub_needs_retry = True
    obj.save(send=False)


@app.task(queue='site-worker')
def delete_from_chahub(app_label, pk):
    if not settings.CHAHUB_API_URL:
        raise ChahubException("CHAHUB_API_URL env var required to send to Chahub")
    if not settings.CHAHUB_API_KEY:
        raise ChahubException("No ChaHub API Key provided")

    obj = get_obj(app_label, pk, include_deleted=True)

    url = f"{settings.CHAHUB_API_URL}{obj.get_chahub_endpoint()}{pk}/"
    logger.info(f"ChaHub :: Sending to ChaHub ({url}) delete message")

    headers = {'X-CHAHUB-API-KEY': settings.CHAHUB_API_KEY}

    try:
        resp = requests.delete(url=url, headers=headers)
    except requests.exceptions.RequestException:
        resp = None

    if resp and resp.status_code == 204:
        logger.info(f"ChaHub :: Received response {resp.status_code} {resp.content}")
        obj.delete()
    else:
        status = getattr(resp, 'status_code', 'N/A')
        body = getattr(resp, 'content', 'N/A')
        logger.info(f"ChaHub :: Error sending to chahub, status={status}, body={body}")
        obj.chahub_needs_retry = True
        obj.save(send=False)


def batch_send_to_chahub(model, limit=None, retry_only=False):
    qs = model.objects.all()
    if retry_only:
        qs = qs.filter(chahub_needs_retry=True)
    if limit is not None:
        qs = qs[:limit]

    endpoint = model.get_chahub_endpoint()
    data = [obj.clean_private_data(obj.get_chahub_data()) for obj in qs if obj.get_chahub_is_valid()]
    if not data:
        logger.info(f'Nothing to send to Chahub at {endpoint}')
        return
    try:
        logger.info(f"Sending all data to Chahub at {endpoint}")
        resp = _send(endpoint=endpoint, data=data)
        logger.info(f"Response Status Code: {resp.status_code}")
        if resp.status_code != 201:
            logger.warning(f'ChaHub Response Content: {resp.content}')
    except ChahubException:
        logger.info("There was a problem reaching Chahub. Retry again later")


def chahub_is_up():
    if not settings.CHAHUB_API_URL:
        return False

    logger.info("Checking whether ChaHub is online before sending retries")
    try:
        response = requests.get(settings.CHAHUB_API_URL)
        if response.ok:
            logger.info("ChaHub is online")
            return True
        else:
            logger.info("Bad Status from ChaHub")
            return False
    except requests.exceptions.RequestException:
        # This base exception works for HTTP errors, Connection errors, etc.
        logger.info("Request Exception trying to access ChaHub")
        return False


def get_chahub_models():
    from chahub.models import ChaHubSaveMixin
    return ChaHubSaveMixin.__subclasses__()


@app.task(queue='site-worker')
def do_chahub_retries(limit=None):
    if not chahub_is_up():
        return
    logger.info("ChaHub is online, checking for objects needing to be re-sent to ChaHub")
    chahub_models = get_chahub_models()
    logger.info(f'Retrying for ChaHub models: {chahub_models}')
    for model in chahub_models:
        batch_send_to_chahub(model, retry_only=True, limit=limit)
        for obj in model.objects.get_all_objects().filter(deleted=True):
            obj.delete()


@app.task(queue='site-worker')
def send_everything_to_chahub(limit=None):
    if not chahub_is_up():
        return
    chahub_models = get_chahub_models()
    for model in chahub_models:
        batch_send_to_chahub(model, limit=limit)
