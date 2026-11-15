"""
Published competitions for the public competitions page and the public competitions API.
Why one place: the page and the API must filter and sort the same way.
"""
from datetime import datetime

import pytz
from django.db.models import Q
from django.utils import dateformat

from .models import Competition, CompetitionParticipant, TagCategory

# Date format of the date pills, for example Jan 1, 2026
PILL_DATE_FORMAT = "M j, Y"

# How the filters combine (filter_mode in the URL and the API).
# Why and/or as values: the API and the dashboard already send them. The page shows them as Any filter and All filters.
FILTER_MODE_OR = 'or'    # Any filter: a competition must match at least one filter
FILTER_MODE_AND = 'and'  # All filters: a competition must match every filter
DEFAULT_FILTER_MODE = FILTER_MODE_OR

# Match buttons on the page: URL value, label, and the help line shown when it is selected.
# Any filter comes first, as the default.
FILTER_MODE_OPTIONS = [
    (FILTER_MODE_OR, "Any filter", "Competitions must match at least one filter or tag you pick. The search and dates still apply."),
    (FILTER_MODE_AND, "All filters", "Competitions must match every filter and tag you pick."),
]

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


def get_public_competitions(user, search='', ordering=DEFAULT_ORDERING, participating_in=False, organizing=False,
                            has_a_prize=False, tag_ids=None, filter_mode=DEFAULT_FILTER_MODE, start_date=None, end_date=None):
    """
    Return the published competitions that match the search, the dates and the filters, sorted.

    The search and the dates always make the list shorter.
    The filters (tags, has_a_prize, participating_in, organizing) are combined by filter_mode:
    - 'and': a competition must match every filter that is on.
    - 'or': a competition must match at least one filter that is on.
    Example: with has_a_prize and organizing on, 'and' shows only the competitions the user organizes
    that have a prize. 'or' shows the ones with a prize plus all the ones the user organizes.

    The participating_in and organizing filters need a logged-in user.
    This function does not check it. Why: the page turns these filters off
    for logged-out visitors, and the API returns an error before calling it.

    :param user: The user who looks at the list.
    :param search: Text to find in the title, or in the creator's username or display name. Empty means no search.
    :param ordering: One of the ORDERINGS keys. An unknown value uses DEFAULT_ORDERING.
    :param participating_in: Only competitions the user takes part in, without the ones the user organizes.
    :param organizing: Only competitions the user created or co-organizes.
    :param has_a_prize: Only competitions with a prize (a reward that is not empty).
    :param tag_ids: Ids of the selected tags. Empty or None means no tag filter.
    :param filter_mode: 'and' or 'or'. Any other value works as 'or'.
    :param start_date: Only competitions created at or after this datetime. None means no start date.
    :param end_date: Only competitions created at or before this datetime. None means no end date.
    :rtype: QuerySet
    """
    competitions = Competition.objects.filter(published=True).select_related('created_by').prefetch_related('tags__category')

    if search:
        competitions = competitions.filter(
            Q(title__icontains=search) |
            Q(created_by__username__icontains=search) |
            Q(created_by__display_name__icontains=search)
        )

    if start_date:
        competitions = competitions.filter(created_when__gte=start_date)
    if end_date:
        competitions = competitions.filter(created_when__lte=end_date)

    participant_competition_ids = None
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

    if filter_mode == FILTER_MODE_AND:
        for tag_id in tag_ids or []:
            # A competition must have every selected tag, so each tag gets its own filter.
            # Example: with Vision and NLP selected, a competition needs a Vision tag and an NLP tag.
            # Why not both ids in one filter: Django would check both ids against the same tag,
            # and a tag has only one id, so no competition would match.
            competitions = competitions.filter(tags__id=tag_id)
        if has_a_prize:
            competitions = competitions.exclude(reward__isnull=True).exclude(reward__exact='')
        if participating_in:
            competitions = competitions.filter(id__in=participant_competition_ids)
        if organizing:
            competitions = competitions.filter(Q(created_by=user) | Q(collaborators=user))
        # Why distinct: filtering on tags or co-organizers can list the same competition more than once.
        if tag_ids or organizing:
            competitions = competitions.distinct()
    else:
        # A competition is kept if it matches any filter that is on.
        # Q() is an empty condition: adding the first filter to it gives just that filter.
        any_condition = Q()
        if tag_ids:
            any_condition |= Q(tags__id__in=tag_ids)
        if has_a_prize:
            any_condition |= ~Q(reward__isnull=True) & ~Q(reward__exact='')
        if participating_in:
            any_condition |= Q(id__in=participant_competition_ids)
        if organizing:
            any_condition |= Q(created_by=user) | Q(collaborators=user)

        # Why the if: an empty Q() means no filter is on, so the list stays as it is
        if any_condition:
            # Why distinct: filtering on tags or co-organizers can list the same competition more than once.
            competitions = competitions.filter(any_condition).distinct()

    order_fields = ORDERINGS.get(ordering, ORDERINGS[DEFAULT_ORDERING])
    return competitions.order_by(*order_fields)


def read_tag_ids(values):
    """
    Turn the tags values of the URL into a list of tag ids.
    The page and the API both use it, and it accepts the two usual ways to send a list:
    - repeated: ?tags=1&tags=3 gives the values ["1", "3"]
    - with commas: ?tags=1,3 gives the value ["1,3"]
    Both return [1, 3], and they can be mixed: ?tags=1,3&tags=7 returns [1, 3, 7].
    Values that are not numbers are skipped, and each id is kept once.

    :param values: All the tags values of the URL, from params.getlist('tags'). An empty list returns [].
    :rtype: list of int
    """
    tag_ids = []
    for value in values:
        for part in value.split(','):
            try:
                tag_id = int(part.strip())
            except ValueError:
                continue
            if tag_id not in tag_ids:
                tag_ids.append(tag_id)
    return tag_ids


def read_date(text, end_of_day=False):
    """
    Turn a date of the URL into a UTC datetime, at the start or the end of that day.
    The date boxes only give a day, but competitions are saved with a time, so the day needs a time to compare with.
    - As a start date: the first moment of the day. "2026-11-12" returns 2026-11-12 00:00:00 UTC.
    - As an end date (end_of_day=True): the last moment of the day. "2026-11-12" returns 2026-11-12 23:59:59 UTC.
    Why the last moment for an end date: with 00:00:00, a competition created on Nov 12 at 15:30
    would be left out of "To: Nov 12", because 15:30 is later than midnight.

    :param text: Date as YYYY-MM-DD. Empty text, None or an invalid date returns None.
    :param end_of_day: True for the last second of the day instead of the first.
    :rtype: datetime or None
    """
    if not text:
        return None
    try:
        day = datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        return None
    if end_of_day:
        day = day.replace(hour=23, minute=59, second=59)
    return day.replace(tzinfo=pytz.UTC)


def read_filters(params, user):
    """
    Read the search, sort and filters of the public competitions page from the URL.
    Unknown sort values use DEFAULT_ORDERING.
    For a logged-out visitor, participating_in and organizing are always off, even if the URL turns them on.
    Why: these filters show the visitor's own competitions. A logged-out visitor has no account, so there is nothing to show.

    The Match switch is Any filter unless the URL has filter_mode=and.
    Invalid tags and dates are skipped, for example tags=abc or start_date=2026-13-45.

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
        'has_a_prize': params.get('has_a_prize') == 'true',
        'tag_ids': read_tag_ids(params.getlist('tags')),
        'filter_mode': FILTER_MODE_AND if params.get('filter_mode') == FILTER_MODE_AND else DEFAULT_FILTER_MODE,
        'start_date': read_date(params.get('start_date')),
        'end_date': read_date(params.get('end_date'), end_of_day=True),
    }


def query_string_without(params, *keys):
    """
    Return the values of the current URL as text, with some of them left out.

    Example: the URL has "search=vision&has_a_prize=true&page=2".
    query_string_without(params, 'page') returns "search=vision&has_a_prize=true".

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


def query_string_without_tag(params, tag_ids, tag_id):
    """
    Return the values of the current URL as text, with one tag left out, for the ✕ of a tag pill.
    The other tags are written as tags=7&tags=9. Also leaves out the page number, so the list starts again on page 1.

    Example: the URL has "tags=3&tags=7&page=2", or "tags=3,7&page=2".
    query_string_without_tag(params, [3, 7], 3) returns "tags=7" for both.
    Why from tag_ids and not from the URL text: with tags=3,7 the URL value is "3,7", not "3".

    :param params: The query parameters of the request (request.GET).
    :param tag_ids: Ids of the selected tags, from read_filters.
    :param tag_id: Id of the tag to leave out.
    :rtype: str
    """
    query = params.copy()
    query.pop('page', None)
    query.setlist('tags', [str(kept) for kept in tag_ids if kept != tag_id])
    return query.urlencode()


def get_tag_categories(selected_tag_ids):
    """
    Return the tag categories with their tags, for the tag dropdowns of the Filters panel.
    One dropdown for each category, with a checkbox for each of its tags.
    The categories keep the order they were created in, and the tags are sorted A to Z.
    A category without tags is left out.

    Example: [{'name': 'Conference', 'selected_count': 1,
               'tags': [{'id': 31, 'name': 'ACL', 'is_selected': False},
                        {'id': 30, 'name': 'NeurIPS', 'is_selected': True}]}]

    selected_count: how many tags of the category are ticked, shown as a number on its dropdown button.
    is_selected: whether the tag is ticked, so its checkbox is ticked again after the page reloads.

    :param selected_tag_ids: Ids of the selected tags, from read_filters.
    :rtype: list of dicts with name, selected_count and tags
    """
    tag_categories = []
    for category in TagCategory.objects.order_by('id').prefetch_related('tags'):
        tags = [
            {'id': tag.id, 'name': tag.name, 'is_selected': tag.id in selected_tag_ids}
            for tag in sorted(category.tags.all(), key=lambda tag: tag.name.lower())
        ]
        if tags:
            tag_categories.append({
                'name': category.name,
                'selected_count': sum(tag['is_selected'] for tag in tags),
                'tags': tags,
            })
    return tag_categories


def get_filter_mode_options(filter_mode):
    """
    Return the Match buttons of the Filters panel, one for each mode in FILTER_MODE_OPTIONS.
    Example: with filter_mode 'or', the Any filter button has is_selected True,
    and its help line is the one shown under the buttons.

    :param filter_mode: The mode in use, from read_filters.
    :rtype: list of dicts with value, label, help and is_selected
    """
    return [
        {'value': value, 'label': label, 'help': help_text, 'is_selected': value == filter_mode}
        for value, label, help_text in FILTER_MODE_OPTIONS
    ]


def put_matching_tags_first(competitions, selected_tag_ids):
    """
    On each card, move the tags the visitor filters by to the front, and mark them with is_match.
    Example: a card has the tags A, B, C, F and the visitor filters by F: the card gets F, A, B, C,
    with F marked, so the card shows it in light blue.
    Why first: the card hides the tags that do not fit from the end, so a matching tag is never hidden in +N more.

    :param competitions: The cards, from HomePageBenchmarkSerializer. They are changed in place.
    :param selected_tag_ids: Ids of the selected tags, from read_filters.
    :rtype: the same competitions
    """
    for competition in competitions:
        for tag in competition['tags']:
            tag['is_match'] = tag['id'] in selected_tag_ids
        matching = [tag for tag in competition['tags'] if tag['is_match']]
        others = [tag for tag in competition['tags'] if not tag['is_match']]
        competition['tags'] = matching + others
    return competitions


def count_active_filters(filters):
    """
    Return the number shown on the Filters button: the checkboxes that are on, the dates that are set,
    and the selected tags. The search and the Match switch do not count, they are not filters of the panel.
    Example: Has reward, a start date and 2 tags return 4.

    :param filters: The dict from read_filters.
    :rtype: int
    """
    checkboxes = [filters['participating_in'], filters['organizing'], filters['has_a_prize']]
    dates = [filters['start_date'], filters['end_date']]
    return sum(bool(value) for value in checkboxes + dates) + len(filters['tag_ids'])


def get_filter_pills(params, filters, tag_categories):
    """
    Return the pills shown under the toolbar: one for the search text and one for each filter that is on.

    Each pill has a prefix, a label and the link of its ✕. The prefix says what the pill is about
    and is shown in grey, for example "Conference:" in front of "NeurIPS". It is empty for the checkboxes.
    The link keeps the sort and the other filters, leaves out only this pill's filter, and leaves out
    the page number, so the list starts again on page 1.
    Example: on "search=vision&has_a_prize=true&page=2", the Has a prize pill links to "search=vision".

    Why the pills: the visitor sees which search and filters are on, even when the Filters panel is closed,
    and can remove one with a single click.

    :param params: The query parameters of the request (request.GET).
    :param filters: The dict from read_filters.
    :param tag_categories: The list from get_tag_categories. Why: the tag pills take the tag and category
        names from it, with no extra query. A tag id in the URL that does not exist gets no pill.
    :rtype: list of dicts with prefix, label and query
    """
    pills = []
    if filters['search']:
        pills.append({'prefix': "Search:", 'label': filters['search'], 'query': query_string_without(params, 'page', 'search')})

    # URL name -> pill label
    filter_labels = [
        ('participating_in', "Participating in"),
        ('organizing', "Organizing"),
        ('has_a_prize', "Has a prize"),
    ]
    for name, label in filter_labels:
        if filters[name]:
            pills.append({'prefix': "", 'label': label, 'query': query_string_without(params, 'page', name)})

    # URL name -> pill prefix
    date_prefixes = [
        ('start_date', "Created from:"),
        ('end_date', "Created to:"),
    ]
    for name, prefix in date_prefixes:
        if filters[name]:
            label = dateformat.format(filters[name], PILL_DATE_FORMAT)
            pills.append({'prefix': prefix, 'label': label, 'query': query_string_without(params, 'page', name)})

    for category in tag_categories:
        for tag in category['tags']:
            if tag['is_selected']:
                pills.append({
                    'prefix': f"{category['name']}:",
                    'label': tag['name'],
                    'query': query_string_without_tag(params, filters['tag_ids'], tag['id']),
                })
    return pills
