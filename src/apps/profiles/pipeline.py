"""Steps added to the social auth pipeline (sign in with GitHub). The pipeline is in SOCIAL_AUTH_PIPELINE."""
from .usernames import generate_unique_username


def get_username(details, user=None, *args, **kwargs):
    """
    Picks the username of a new user, before create_user saves it.
    Why: without this step, the GitHub login is saved as it is, for example 'John.Doe'.
    Its slug is 'johndoe', so the profile links differ, and the save fails when the username or the slug is taken.
    """
    # Users who already have an account keep their username
    if user:
        return None

    name = details.get('username') or (details.get('email') or '').split('@')[0]
    return {'username': generate_unique_username(name)}
