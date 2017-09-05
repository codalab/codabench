

def user_details(user, **kwargs):
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
