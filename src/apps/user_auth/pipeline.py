from .models import User


# def get_username(strategy, uid, user=None, *args, **kwargs):
#     # """If no user, set username to UID."""
#     # if not user:
#     #     username = uid
#     # else:
#     #     username = strategy.storage.user.get_username(user)
#     print("Uid", uid)
#     print("User", user)
#     username = 'whatever'
#     return {'username': username}


def user_details(user, details, strategy, *args, **kwargs):
    """Update user details using data from provider."""
    if user:
        changed = False  # flag to track changes
        user_attrs = [
            'avatar_url',
            'url',
            'html_url',
            'name',
            'company',
            'bio',
            'email',
        ]
        if kwargs:
            try:
                response = kwargs.pop("response")
                for attr in user_attrs:
                    user_attr_value = getattr(user, attr, None)
                    github_attr_value = response[attr]
                    if not user_attr_value:
                        setattr(user, attr, github_attr_value)
                # Set the ID github returns to UID on user.
                setattr(user, 'uid', response['id'])
                user.save()
            except AttributeError:
                print("Attribute not found.")
        if changed:
            strategy.storage.user.changed(user)


def associate_existing_user(uid, *args, **kwargs):
    """If there already is a user with the given uid, hand it over to the pipeline"""
    if User.objects.filter(uid=uid).exists():
        print("User already found: {}".format(uid))
        return {
            'user': User.objects.get(uid=uid)
        }
