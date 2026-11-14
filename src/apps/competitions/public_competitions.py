"""
Published competitions for the public competitions page and the public competitions API.
Why one place: the page and the API must filter and sort the same way.
"""
from django.db.models import Q
from .models import Competition, CompetitionParticipant

# Sort value in the URL -> fields to order by.
# -id decides the order when competitions have the same number, for example the same
# number of participants: the newest comes first.
# Why: without it, the database decides the order of these ties, and it can change between
# requests. Each page is a new request, so a competition could show on two pages
# and another one on none of them.
ORDERINGS = {
    'recent': ('-id',),
    'popular': ('-participants_count', '-id'),
    'with_most_submissions': ('-submissions_count', '-id'),
}
DEFAULT_ORDERING = 'recent'

# Sort menu on the page: URL value and label
SORT_OPTIONS = [
    ('recent', 'Most recent'),
    ('popular', 'Most popular'),
    ('with_most_submissions', 'Most submissions'),
]


def get_public_competitions(user, search='', ordering=DEFAULT_ORDERING, participating_in=False, organizing=False, has_reward=False):
    """
    Return the published competitions that match the filters, sorted.

    The participating_in and organizing filters need a logged-in user.
    This function does not check it. Why: the page turns these filters off
    for logged-out visitors, and the API returns an error before calling it.

    :param user: The user who looks at the list.
    :param search: Text to find in the title. Empty means no search.
    :param ordering: One of the ORDERINGS keys. An unknown value uses DEFAULT_ORDERING.
    :param participating_in: Only competitions the user takes part in, without the ones the user organizes.
    :param organizing: Only competitions the user created or co-organizes.
    :param has_reward: Only competitions with a reward.
    :rtype: QuerySet
    """
    competitions = Competition.objects.filter(published=True).select_related('created_by')

    if search:
        competitions = competitions.filter(title__icontains=search)

    if participating_in:
        # The creator and the co-organizers of a competition are also saved as approved participants
        # (see Competition.save()).
        # Why the exclude: without it, Participating in would also list the competitions the user organizes.
        # Those already have their own filter, Organizing.
        participant_competition_ids = CompetitionParticipant.objects.filter(
            user=user,
            status="approved",
        ).exclude(
            Q(competition__created_by=user) | Q(competition__collaborators=user)
        ).values_list("competition_id", flat=True)
        competitions = competitions.filter(id__in=participant_competition_ids)

    if organizing:
        competitions = competitions.filter(Q(created_by=user) | Q(collaborators=user)).distinct()

    if has_reward:
        competitions = competitions.exclude(reward__isnull=True).exclude(reward__exact='')

    order_fields = ORDERINGS.get(ordering, ORDERINGS[DEFAULT_ORDERING])
    return competitions.order_by(*order_fields)


def read_filters(params, user):
    """
    Read the search, sort and filters of the public competitions page from the URL.
    Unknown sort values use DEFAULT_ORDERING.
    For a logged-out visitor, participating_in and organizing are always off, even if the URL turns them on.
    Why: these filters show the visitor's own competitions. A logged-out visitor has no account, so there is nothing to show.

    :param params: The query parameters of the request (request.GET).
    :param user: The user who looks at the page.
    :rtype: dict, with the same keys as the get_public_competitions arguments (without user)
    """
    ordering = params.get('ordering')
    return {
        'search': params.get('search', '').strip(),
        'ordering': ordering if ordering in ORDERINGS else DEFAULT_ORDERING,
        'participating_in': user.is_authenticated and params.get('participating_in') == 'true',
        'organizing': user.is_authenticated and params.get('organizing') == 'true',
        'has_reward': params.get('has_reward') == 'true',
    }


def query_string_without(params, *keys):
    """
    Return the values of the current URL as text, with some of them left out.

    Example: the URL has "search=vision&has_reward=true&page=2".
    query_string_without(params, 'page') returns "search=vision&has_reward=true".

    Why: the page builds its links from this text. For example, the Next link adds a new page
    number, and the ✕ on a filter pill leaves that one filter out. The other values stay,
    so the visitor keeps their search and filters.

    :param params: The query parameters of the request (request.GET).
    :param keys: Names of the parameters to leave out.
    :rtype: str
    """
    query = params.copy()
    for key in keys:
        query.pop(key, None)
    return query.urlencode()


def get_sort_options(params, ordering):
    """
    Return the options of the Sort menu, one for each sort in SORT_OPTIONS.

    Each option has the link it opens. The link keeps the current search and filters,
    sets that sort, and leaves out the page number, so the list starts again on page 1.
    Example: on "search=vision&page=3", the Most popular option links to
    "search=vision&ordering=popular".

    Why page 1: after a new sort, page 3 shows different competitions, so the visitor
    starts again at the top.

    :param params: The query parameters of the request (request.GET).
    :param ordering: The sort in use.
    :rtype: list of dicts with label, query and is_selected
    """
    sort_options = []
    for value, label in SORT_OPTIONS:
        query = params.copy()
        query.pop('page', None)
        query['ordering'] = value
        sort_options.append({
            'label': label,
            'query': query.urlencode(),
            'is_selected': value == ordering,
        })
    return sort_options


def get_filter_pills(params, filters):
    """
    Return the pills shown under the toolbar: one for the search text and one for each filter that is on.

    Each pill has a label and the link of its ✕. The link keeps the sort and the other filters,
    leaves out only this pill's filter, and leaves out the page number, so the list starts again on page 1.
    Example: on "search=vision&has_reward=true&page=2", the Has reward pill links to "search=vision".

    Why the pills: the visitor sees which search and filters are on, even when the Filters panel is closed,
    and can remove one with a single click.

    :param params: The query parameters of the request (request.GET).
    :param filters: The dict from read_filters.
    :rtype: list of dicts with label and query
    """
    pills = []
    if filters['search']:
        pills.append({'label': f"Search: {filters['search']}", 'query': query_string_without(params, 'page', 'search')})

    # URL name -> pill label
    filter_labels = [
        ('participating_in', "Participating in"),
        ('organizing', "Organizing"),
        ('has_reward', "Has reward"),
    ]
    for name, label in filter_labels:
        if filters[name]:
            pills.append({'label': label, 'query': query_string_without(params, 'page', name)})
    return pills
