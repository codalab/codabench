from django.conf import settings

import logging
import requests
import json

logger = logging.getLogger(__name__)


class ChahubException(Exception):
    pass


def send_to_chahub(endpoint, data):
    """
    Does a post request to the specified API endpoint on chahub with the inputted data.
    :param endpoint: String designating which API endpoint; IE: 'producers/'
    :param data: Dictionary containing data we are sending away to the endpoint.
    :param update: If updating, send PUT request to update the object, else send POST request to create it.
    :return:
    """
    if not endpoint:
        raise ChahubException("No ChaHub API endpoint given")
    if not settings.CHAHUB_API_URL:
        raise ChahubException("CHAHUB_API_URL env var required to send to Chahub")

    url = f"{settings.CHAHUB_API_URL}{endpoint}"

    data = json.dumps(data)

    logger.info(f"ChaHub :: Sending to ChaHub ({url}) the following data: \n{data}")
    try:
        kwargs = {
            'url': url,
            'headers': {
                'Content-type': 'application/json',
                'X-CHAHUB-API-KEY': settings.CHAHUB_API_KEY,
            }
        }
        return requests.post(data=data, **kwargs)
    except requests.ConnectionError:
        raise ChahubException('Connection Error with ChaHub')


def get_all_chahub_user_data():
    from profiles.models import User
    all_users = User.objects.all()
    user_data_list = []
    for user in all_users:
        user_data_list.append(user.get_chahub_data())
    return user_data_list
