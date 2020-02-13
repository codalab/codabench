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

    if 'HTTP_HOST' in request.META:
        host = request.META['HTTP_HOST'].split(':')[0]
    else:
        host = 'localhost'

    return {
        'STORAGE_TYPE': settings.STORAGE_TYPE,
        'USER_JSON_DATA': json.dumps(user_json_data),
        'RABBITMQ_MANAGEMENT_URL': f"{host}:{settings.RABBITMQ_MANAGEMENT_PORT}",
        'FLOWER_URL': f"{host}:{settings.FLOWER_PORT}",
    }
