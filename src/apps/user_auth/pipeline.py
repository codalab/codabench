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
    backend = kwargs.get('backend')

    if user:
        if backend and backend.name == 'codalab':
            # user.save()  # Probably not necessary? was here to stop NoneType exception
            pass
        else:
            user_attrs = [
                'avatar_url',
                'url',
                'html_url',
                'name',
                'company',
                'bio',
                'email',
            ]

            response = kwargs.pop("response")
            for attr in user_attrs:
                if not getattr(user, attr):
                    setattr(user, attr, response[attr])

            # Set the ID github returns to UID on user.
            user.github_uid = response['id']
            user.save()


def associate_existing_user(uid, *args, **kwargs):
    """If there already is a user with the given uid, hand it over to the pipeline"""
    if User.objects.filter(uid=uid).exists():
        print("User already found: {}".format(uid))
        return {
            'user': User.objects.get(uid=uid)
        }
