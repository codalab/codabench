from requests import HTTPError

from six.moves.urllib.parse import urljoin

from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthFailed



BASE_URL = "https://competitions-v2-staging-pr-17.herokuapp.com"


class CodalabOAuth2(BaseOAuth2):
    """Github OAuth authentication backend"""
    name = 'codalab'
    API_URL = '{}/api/'.format(BASE_URL)
    AUTHORIZATION_URL = '{}/oauth/authorize/'.format(BASE_URL)
    ACCESS_TOKEN_URL = '{}/oauth/token/'.format(BASE_URL)
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_details(self, response):
        access_token = response['access_token']
        my_profile_url = "{}my_profile/".format(self.API_URL)
        data = self.get_json(my_profile_url, params={'Authorization: Bearer': access_token})
        print("usa details", data)
        return {
            'username': data.username,
            'email': data.email,
            'name': data.name,
        }
