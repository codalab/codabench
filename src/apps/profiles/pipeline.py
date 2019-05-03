

def user_details(user, **kwargs):
    """Update user details using data from provider."""
    backend = kwargs.get('backend')

    if user:
        if backend and backend.name == 'chahub':
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

            user.save()
