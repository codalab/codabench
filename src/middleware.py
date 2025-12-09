from django.shortcuts import render
from django.http import JsonResponse


class BlockBannedUsersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and user.is_banned:
            # For api paths return json response
            # For normal paths show banned page
            if request.path.startswith("/api/"):
                return JsonResponse({"error": "You are banned from using Codabench"}, status=403)
            else:
                return render(request, "banned.html", status=403)

        return self.get_response(request)
