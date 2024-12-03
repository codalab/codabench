'''
This file contains utilities for competitions
'''
import random
# from django.db.models import Count

from competitions.models import Competition


def get_popular_competitions(limit=4):
    '''
    Function to return most popular competitions based on the amount of participants.

    :param limit: Amount of competitions to return. Default is 3.
    :rtype: list
    :return:  Most popular competitions.
    '''

    competitions = Competition.objects.filter(published=True) \
        .order_by('-participants_count')

    if len(competitions) <= limit:
        return competitions

    return competitions[:limit]


def get_featured_competitions(limit=4):
    '''
    Function to return featured competitions

    :param limit: Amount of competitions to return. Default is 4
    :rtype: list
    :return: list of featured competitions
    '''

    competitions = Competition.objects.filter(is_featured=True)

    if len(competitions) <= limit:
        return competitions
    else:
        return random.sample(list(competitions), limit)
