from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class BasicPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000


class LargePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000

    # Writing custom response so we can pass 'page_size' to front-end so it can calculate total number of pages.
    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'page_size': self.page_size,
            'results': data
        })


class DynamicChoicePagination(PageNumberPagination):
    """
    Pagination dynamique pour l'UI :
    - défaut : 50
    - valeurs autorisées côté client : 50, 100, 500, all
    - si page_size=all => on renvoie tous les objets (dans la limite de max_page_size)
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000
    _allowed_sizes = (50, 100, 500, 'all')

    def get_page_size(self, request):
        raw = request.query_params.get(self.page_size_query_param)
        if raw is None:
            return self.page_size

        raw_lower = str(raw).lower()
        if raw_lower == 'all':
            return None

        try:
            val = int(raw)
        except (TypeError, ValueError):
            return self.page_size

        if val in (50, 100, 500):
            return val
        return self.page_size

    def paginate_queryset(self, queryset, request, view=None):
        raw = request.query_params.get(self.page_size_query_param)
        self.requested_page_size = raw if raw is not None else str(self.page_size)

        if raw is not None and str(raw).lower() == 'all':
            try:
                total = queryset.count()
            except Exception:
                total = self.max_page_size
            self.page_size = total if (isinstance(total, int) and total > 0) else 1
        else:
            page_size = self.get_page_size(request)
            if page_size is None:
                page_size = self.page_size
            self.page_size = page_size

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        page_size_value = self.requested_page_size if getattr(self, 'requested_page_size', None) is not None else self.page_size

        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'page_size': page_size_value,
            'results': data,
            'allowed_page_sizes': [50, 100, 500, 'all'],
        })