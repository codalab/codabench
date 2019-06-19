'''
This file contains utilities for competitions
'''
import random

from django.db.models import Count

from competitions.models import Competition


def get_popular_competitions(limit=3):
    '''
    Function to return most popular competitions based on the amount of participants.

    :param limit: Amount of competitions to return. Default is 3.
    :rtype: list
    :return:  Most popular competitions.
    '''
    competitions = Competition.objects.filter(published=True) \
        .annotate(participant_count=Count('participants')) \
        .order_by('-participant_count')

    if len(competitions) <= limit:
        return competitions

    return competitions[:limit]


def get_featured_competitions(limit=3, excluded_competitions=None):
    '''
    Function to return featured competitions if they are still open.

    :param limit: Amount of competitions to return. Default is 3
    :param excluded_competitions: list of popular competitions to prevent displaying duplicates
    :rtype: list
    :return: list of featured competitions
    '''

    competitions = Competition.objects.filter(published=True) \
        .annotate(participant_count=Count('participants'))

    if excluded_competitions:
        competitions = competitions.exclude(pk__in=[c.pk for c in excluded_competitions])

    if len(competitions) <= limit:
        return competitions
    else:
        return random.sample(list(competitions), limit)
