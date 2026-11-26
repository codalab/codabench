from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView

from papers.models import Paper


SORT_CHOICES = (
    ('recent', 'Most recent', ('-publication_date', '-citation_count', '-id')),
    ('citations', 'Most cited', ('-citation_count', '-publication_date', '-id')),
    ('oldest', 'Oldest', ('publication_date', '-citation_count', 'id')),
)
SORT_MAP = {key: (label, fields) for key, label, fields in SORT_CHOICES}
DEFAULT_ORDERING = 'recent'


def _build_query(params, **overrides):
    # Rebuild the current query string with single-key overrides (used by sort links and filter pills)
    merged = {k: v for k, v in params.items() if v}
    for k, v in overrides.items():
        if v is None or v == '':
            merged.pop(k, None)
        else:
            merged[k] = v
    return urlencode(merged)


class HallOfPapersView(TemplateView):
    template_name = 'papers/list.html'
    papers_per_page = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        req = self.request.GET

        search = (req.get('search') or '').strip()
        start_date = parse_date(req.get('start_date') or '')
        end_date = parse_date(req.get('end_date') or '')
        raw_min_cit = (req.get('min_citations') or '').strip()
        min_citations = int(raw_min_cit) if raw_min_cit.isdigit() and int(raw_min_cit) > 0 else None

        ordering = req.get('ordering') or DEFAULT_ORDERING
        if ordering not in SORT_MAP:
            ordering = DEFAULT_ORDERING

        qs = Paper.objects.filter(is_visible=True)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(authors__icontains=search) |
                Q(venue__icontains=search)
            )
        if start_date:
            qs = qs.filter(publication_date__gte=start_date)
        if end_date:
            qs = qs.filter(publication_date__lte=end_date)
        if min_citations is not None:
            qs = qs.filter(citation_count__gte=min_citations)

        selected_sort_label, order_fields = SORT_MAP[ordering]
        qs = qs.order_by(*order_fields)

        base_params = {
            'search': search,
            'start_date': start_date.isoformat() if start_date else '',
            'end_date': end_date.isoformat() if end_date else '',
            'min_citations': str(min_citations) if min_citations is not None else '',
            'ordering': ordering if ordering != DEFAULT_ORDERING else '',
        }

        # Filter pills (each removes that single filter)
        filter_pills = []
        if search:
            filter_pills.append({'prefix': 'Search:', 'label': search, 'query': _build_query(base_params, search=None)})
        if start_date:
            filter_pills.append({'prefix': 'From:', 'label': start_date.isoformat(), 'query': _build_query(base_params, start_date=None)})
        if end_date:
            filter_pills.append({'prefix': 'To:', 'label': end_date.isoformat(), 'query': _build_query(base_params, end_date=None)})
        if min_citations is not None:
            filter_pills.append({'prefix': 'Citations:', 'label': f'≥ {min_citations}', 'query': _build_query(base_params, min_citations=None)})

        # Badge count covers only filters inside the collapsible Filters panel (excludes search and sort)
        active_filter_count = sum(bool(x) for x in (start_date, end_date, min_citations))

        sort_options = [
            {
                'value': key,
                'label': label,
                'is_selected': key == ordering,
                'query': _build_query(base_params, ordering=None if key == DEFAULT_ORDERING else key),
            }
            for key, label, _ in SORT_CHOICES
        ]

        paginator = Paginator(qs, self.papers_per_page)
        page = paginator.get_page(req.get('page'))

        context.update({
            'papers': page.object_list,
            'total_papers': paginator.count,
            'page': page,
            'page_query': _build_query(base_params),
            'filters': {
                'search': search,
                'start_date': start_date,
                'end_date': end_date,
                'min_citations': min_citations or '',
                'ordering': ordering,
            },
            'default_ordering': DEFAULT_ORDERING,
            'selected_sort_label': selected_sort_label,
            'sort_options': sort_options,
            'filter_pills': filter_pills,
            'active_filter_count': active_filter_count,
            'clear_filters_url': reverse('papers:list'),
        })
        return context
