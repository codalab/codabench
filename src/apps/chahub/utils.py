from django.conf import settings

import logging
import requests
import json

logger = logging.getLogger(__name__)


def send_to_chahub(endpoint, data, update=False):
    """
    Does a post request to the specified API endpoint on chahub with the inputted data.
    :param endpoint: String designating which API endpoint; IE: 'producers/'
    :param data: Dictionary containing data we are sending away to the endpoint.
    :return:
    """
    assert endpoint, Exception("No ChaHub API endpoint given")
    assert settings.CHAHUB_API_URL, "CHAHUB_API_URL env var required to send to Chahub "

    url = "{}{}".format(settings.CHAHUB_API_URL, endpoint)

    data = json.dumps(data)

    logger.info("ChaHub :: Sending to ChaHub ({}) the following data: \n{}".format(url, data))
    try:
        kwargs = {
            'url': url,
            'headers': {
                'Content-type': 'application/json',
                'X-CHAHUB-API-KEY': settings.CHAHUB_API_KEY,
            }
        }
        if update:
            # return requests.patch(data=data, **kwargs)
            return requests.put(data=data, **kwargs)
        else:
            return requests.post(data=data, **kwargs)
    except requests.ConnectionError:
        # TODO: Should this be raising a new exception to be caught later?
        return None


def get_all_chahub_user_data():
    from profiles.models import User
    all_users = User.objects.all()
    user_data_list = []
    for user in all_users:
        user_data_list.append(user.get_chahub_data()[0])
    return user_data_list
