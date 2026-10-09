'''
Benchmarks shown on the home page (Featured, Popular and Recent sections)
'''
import random

from competitions.models import Competition


def get_featured_benchmarks(limit=3):
    """
    Return random published featured benchmarks.
    The Featured section is hidden when this is empty.

    :param limit: Amount of benchmarks to return. Default is 3.
    :rtype: list
    """
    featured = list(Competition.objects.filter(published=True, is_featured=True))
    return random.sample(featured, min(limit, len(featured)))


def get_popular_benchmarks(limit=3, pool_size=8):
    """
    Return random benchmarks picked from the published benchmarks with the most participants.
    Featured benchmarks are left out (they have their own section).

    :param limit: Amount of benchmarks to return. Default is 3.
    :param pool_size: Amount of most popular benchmarks to pick from. Default is 8.
    :rtype: list
    """
    pool = list(Competition.objects.filter(published=True, is_featured=False)
                .order_by('-participants_count')[:pool_size])
    return random.sample(pool, min(limit, len(pool)))


def get_recent_benchmarks(exclude_ids=None, limit=3, pool_size=8):
    """
    Return random benchmarks picked from the latest published benchmarks.
    Featured benchmarks and the given ids (the popular ones already shown) are left out.

    :param exclude_ids: List of competition ids to exclude.
    :param limit: Amount of benchmarks to return. Default is 3.
    :param pool_size: Amount of latest benchmarks to pick from. Default is 8.
    :rtype: list
    """
    pool = list(Competition.objects.filter(published=True, is_featured=False)
                .exclude(id__in=exclude_ids or [])
                .order_by('-created_when')[:pool_size])
    return random.sample(pool, min(limit, len(pool)))
