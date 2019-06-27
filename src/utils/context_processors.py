import json

from django.conf import settings


def common_settings(request):
    if request.user.is_authenticated:
        user_json_data = {
            "id": request.user.id,
            "name": request.user.name,
            "username": request.user.username,
            "email": request.user.email,
            "bio": request.user.bio,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
            "logged_in": request.user.is_authenticated,
        }
    else:
        user_json_data = {"logged_in": False}

    return {
        'STORAGE_TYPE': settings.STORAGE_TYPE,
        'USER_JSON_DATA': json.dumps(user_json_data)
    }
