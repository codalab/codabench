from django.conf import settings


def common_settings(request):
    return {
        'STORAGE_TYPE': settings.STORAGE_TYPE
    }
