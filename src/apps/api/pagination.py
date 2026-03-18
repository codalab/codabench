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
    Dynamic pagination :
    - default : 50 objects.
    - predetermined values : 50, 100, 500, all
    - if page_size=all => fetch all objects, capped by lax_page_size
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
            return self.max_page_size

        try:
            val = int(raw)
        except (TypeError, ValueError):
            return self.page_size
    
        if val in (50, 100, 500):
            return min(val, self.max_page_size)
        return self.page_size

    def paginate_queryset(self, queryset, request, view=None):
        raw = request.query_params.get(self.page_size_query_param)
        self.requested_page_size = str(raw).lower() if raw is not None else str(self.page_size)

        page_size = self.get_page_size(request)
        if isinstance(page_size, int) and page_size > 0:
            self.page_size = min(page_size, self.max_page_size)
        else:
            self.page_size = self.page_size

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        page_size_value = getattr(self, 'requested_page_size', None)
        if page_size_value is None:
            page_size_value = self.page_size

        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'page_size': page_size_value,
            'results': data,
            'allowed_page_sizes': [50, 100, 500, 'all'],
        })
