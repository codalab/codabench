from django.shortcuts import render


class BlockBannedUsersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_authenticated and user.is_banned:
            return render(request, "banned.html", status=403)

        return self.get_response(request)
