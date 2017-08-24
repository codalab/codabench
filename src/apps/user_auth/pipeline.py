from .models import User


def get_username(strategy, uid, user=None, *args, **kwargs):
    """Removes unnecessary slugification and cleaning of the username since the uid is unique and well formed"""
    if user:
        username = strategy.storage.user.get_username(user)
    else:
        username = uid
    return {'username': username}


def user_details(user, details, strategy, *args, **kwargs):
    """Update user details using data from provider."""
    if user:
        changed = False  # flag to track changes
        protected = ('id', 'pk') + tuple(strategy.setting('PROTECTED_USER_FIELDS', []))

        # Update user model attributes with the new data sent by the current
        # provider. Update on some attributes is disabled by default, for
        # example username and id fields. It's also possible to disable update
        # on fields defined in SOCIAL_AUTH_PROTECTED_FIELDS.
        if details['user']:
            # print(dir(details['player']))
            for name, value in details['user'].items():
                if value is not None and hasattr(user, name):
                    current_value = getattr(user, name, None)
                    print("Name is {0} Value is {1}".format(name, value))
                    # print(current_value)
                    # print(str(getattr(user, name, None)))
                    if not current_value or name not in protected:
                        changed |= current_value != value
                        setattr(user, name, value)
        if changed:
            strategy.storage.user.changed(user)


def associate_existing_user(uid, *args, **kwargs):
    """If there already is an user with the given steamid, hand it over to the pipeline"""
    if User.objects.filter(uid=uid).exists():
        print(uid)
        return {
            'user': User.objects.get(uid=uid)
        }