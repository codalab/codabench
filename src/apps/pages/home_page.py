"""
Benchmarks shown on the home page (Featured, Popular and Recent sections)
"""
import random

from competitions.models import Competition


def get_featured_benchmarks(limit=3):
    """
    Return random published featured benchmarks.
    The Featured section is hidden when this is empty.

    :param limit: Amount of benchmarks to return. Default is 3.
    :rtype: list
    """
    featured = list(Competition.objects.filter(published=True, is_featured=True)
                    .prefetch_related('tags__category'))
    return random.sample(featured, min(limit, len(featured)))


def keep_one_benchmark_per_organizer(benchmarks, order_by):
    """
    Keep only the first benchmark of each organizer, using the given order.
    Example: with order_by='-participants_count', an organizer with 4 benchmarks
    keeps only their one with the most participants.

    :param benchmarks: Competition queryset to filter.
    :param order_by: Field that decides which benchmark each organizer keeps.
    :rtype: QuerySet
    """
    # Postgres keeps the first row of each organizer when the order starts with created_by
    first_per_organizer = (benchmarks.order_by('created_by', order_by)
                           .distinct('created_by')
                           .values('id'))
    return Competition.objects.filter(id__in=first_per_organizer).order_by(order_by)


def get_popular_benchmarks(limit=3, pool_size=8):
    """
    Return random benchmarks picked from the published benchmarks with the most participants.
    Featured benchmarks are left out (they have their own section).
    Each organizer appears at most once, with their most popular benchmark.

    :param limit: Amount of benchmarks to return. Default is 3.
    :param pool_size: Amount of most popular benchmarks to pick from. Default is 8.
    :rtype: list
    """
    benchmarks = Competition.objects.filter(published=True, is_featured=False)
    pool = list(keep_one_benchmark_per_organizer(benchmarks=benchmarks, order_by='-participants_count')
                .prefetch_related('tags__category')[:pool_size])
    return random.sample(pool, min(limit, len(pool)))


def get_recent_benchmarks(exclude_ids=None, limit=3, pool_size=8):
    """
    Return random benchmarks picked from the latest published benchmarks.
    Featured benchmarks and the given ids (the popular ones already shown) are left out.
    Each organizer appears at most once, with their newest benchmark.

    :param exclude_ids: List of competition ids to exclude.
    :param limit: Amount of benchmarks to return. Default is 3.
    :param pool_size: Amount of latest benchmarks to pick from. Default is 8.
    :rtype: list
    """
    benchmarks = (Competition.objects.filter(published=True, is_featured=False)
                  .exclude(id__in=exclude_ids or []))
    pool = list(keep_one_benchmark_per_organizer(benchmarks=benchmarks, order_by='-created_when')
                .prefetch_related('tags__category')[:pool_size])
    return random.sample(pool, min(limit, len(pool)))
