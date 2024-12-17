import json
import os
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Set the absolute path for the version file
VERSION_FILE_PATH = os.path.join(os.path.dirname(BASE_DIR), 'version.json')
# Set the absolute path for the home page counters file
HOME_PAGE_COUNTERS_FILE_PATH = os.path.join(os.path.dirname(BASE_DIR), 'home_page_counters.json')


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

    # Read version information from the version.json file
    version_info = {}
    try:
        with open(VERSION_FILE_PATH) as version_file:
            version_info = json.load(version_file)
    except FileNotFoundError:
        version_info = {"tag_name": "unknown"}
    except json.JSONDecodeError:
        version_info = {"tag_name": "invalid"}

    # Read home page counters information from the home_page_counters.json file
    home_page_counters_info = {}
    try:
        with open(HOME_PAGE_COUNTERS_FILE_PATH) as counters_file:
            home_page_counters_info = json.load(counters_file)
    except Exception:
        home_page_counters_info = {
            "public_competitions": 0,
            "users": 0,
            "submissions": 0
        }

    return {
        'STORAGE_TYPE': settings.STORAGE_TYPE,
        'MAX_EXECUTION_TIME_LIMIT': settings.MAX_EXECUTION_TIME_LIMIT,
        'USER_JSON_DATA': json.dumps(user_json_data),
        'RABBITMQ_MANAGEMENT_URL': f"http://{settings.DOMAIN_NAME}:{settings.RABBITMQ_MANAGEMENT_PORT}",
        'FLOWER_URL': f"http://{settings.DOMAIN_NAME}:{settings.FLOWER_PUBLIC_PORT}",
        'ENABLE_SIGN_UP': settings.ENABLE_SIGN_UP,
        'ENABLE_SIGN_IN': settings.ENABLE_SIGN_IN,
        'VERSION_INFO': version_info,
        'HOME_PAGE_COUNTERS_INFO': home_page_counters_info
    }
