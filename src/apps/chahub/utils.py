from django.conf import settings

import requests
import json

import logging
logger = logging.getLogger()


class ChahubException(Exception):
    pass


def send_to_chahub(endpoint, data):
    """
    Does a post request to the specified API endpoint on chahub with the inputted data.
    :param endpoint: String designating which API endpoint; IE: 'producers/'
    :param data: Dictionary containing data we are sending away to the endpoint.
    :return:
    """
    if not endpoint:
        raise ChahubException("No ChaHub API endpoint given")
    if not settings.CHAHUB_API_URL:
        raise ChahubException("CHAHUB_API_URL env var required to send to Chahub")

    url = f"{settings.CHAHUB_API_URL}{endpoint}"

    logger.info(f"ChaHub :: Sending to ChaHub ({url}) the following data: \n{data}")
    try:
        headers = {
            'Content-type': 'application/json',
            'X-CHAHUB-API-KEY': settings.CHAHUB_API_KEY,
        }
        return requests.post(url=url, data=json.dumps(data), headers=headers)
    except requests.ConnectionError:
        raise ChahubException('Connection Error with ChaHub')
