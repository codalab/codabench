'''
This file contains utilities for competitions
'''
import datetime

from random import randint

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

    if len(competitions) < 3:
        return competitions

    return competitions[:limit]


def get_featured_competitions(limit=3):
    '''
    Function to return featured competitions if they are still open.

    :param limit: Amount of competitions to return. Default is 3
    :rtype: list
    :return: list of featured competitions
    '''
    featured_competitions = []
    competitions = Competition.objects.filter(published=True) \
        .annotate(participant_count=Count('participants'))
    popular_competitions = get_popular_competitions()
    popular_competitions_pk = [c.pk for c in popular_competitions]
    competitions = competitions.exclude(pk__in=popular_competitions_pk)

    if len(competitions) < 3:
        return competitions
    else:
        while len(featured_competitions) < 3:
            competition = competitions[randint(0, competitions.count() - 1)]
            if competition not in featured_competitions:
                featured_competitions.append(competition)

    return featured_competitions[:limit]
