"""
Rules for usernames, shared by every way to create an account: the sign up form, GitHub and OIDC.

The slug of a user is slugify(username), and it must be unique.
When the two differ, for example 'hello_world__' has the slug 'hello_world', two problems appear:
- another user cannot get the same slug, so creating 'hello_world' failed with a server error
- links built with the username and links built with the slug do not look the same
So a new username must already be its own slug.
"""
from django.db.models import Q
from django.utils.text import slugify

from .models import User


def is_its_own_slug(username):
    """True when slugify keeps the username as it is, for example 'jane_doe', but not 'jane_doe__' or 'Jane'."""
    return slugify(username, allow_unicode=True) == username


def is_taken(username):
    """
    True when a user already has this username, or this slug.
    Why the slug too: an older user 'hello_world__' has the slug 'hello_world', so 'hello_world' cannot be saved.
    Deleted users count too, their username and slug stay in the table.
    """
    return User.objects.filter(Q(username=username) | Q(slug=username)).exists()


def generate_unique_username(name, fallback='user'):
    """
    Turns a name from another site (a GitHub login, an OIDC nickname) into a free username that is its own slug.
    For example 'John.Doe' gives 'johndoe', or 'johndoe_1' when 'johndoe' is taken.
    The fallback is used when nothing is left of the name, for example '!!!'.
    """
    max_length = User._meta.get_field('username').max_length
    # Why strip after cutting: the cut can end the name with '-' or '_', which slugify would remove
    base = slugify(name)[:max_length].strip('-_') or fallback

    username = base
    suffix = 1
    while is_taken(username):
        end = f'_{suffix}'
        username = base[:max_length - len(end)].strip('-_') + end
        suffix += 1
    return username
