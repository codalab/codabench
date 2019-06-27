from profiles.models import GithubUserInfo


def user_details(user, **kwargs):
    """Update user details using data from provider."""
    backend = kwargs.get('backend')

    if user:
        if backend and backend.name == 'chahub':
            if kwargs.get('details', {}).get('github_info'):
                github_info = kwargs['details'].pop('github_info', None)
                if github_info and github_info.get('uid'):
                    obj, created = GithubUserInfo.objects.update_or_create(
                        uid=github_info.pop('uid'),
                        defaults=github_info,
                    )
                    if created:
                        print("New github user info created for user: {}".format(user.username))
        else:
            pass
