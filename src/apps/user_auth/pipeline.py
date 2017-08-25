from .models import User


def get_username(strategy, uid, user=None, *args, **kwargs):
    """Removes unnecessary slugification and cleaning of the username since the uid is unique and well formed"""
    if not user:
        username = uid
    else:
        username = strategy.storage.user.get_username(user)
    return {'username': username}


def user_details(user, details, strategy, *args, **kwargs):
    """Update user details using data from provider."""
    if user:
        changed = False  # flag to track changes
        protected = ('id', 'pk') + tuple(strategy.setting('PROTECTED_USER_FIELDS', []))
        user_attrs = [
            'login' ,
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
                    print("Current attribute is {}".format(attr))
                    user_attr_value = getattr(user, attr, None)
                    github_attr_value = response[attr]
                    if not user_attr_value or attr not in protected:
                        print("Setting value: {0} of attribute: {1} on userid: {2}".format(
                            github_attr_value,
                            attr,
                            user.pk,
                        ))
                        setattr(user, attr, github_attr_value)
                setattr(user, 'uid', response['id'])
                user.save()
            except AttributeError:
                print("Attribute not found.")
        if changed:
            strategy.storage.user.changed(user)


def associate_existing_user(uid, *args, **kwargs):
    """If there already is an user with the given steamid, hand it over to the pipeline"""
    if User.objects.filter(uid=uid).exists():
        print(uid)
        return {
            'user': User.objects.get(uid=uid)
        }
