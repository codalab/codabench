'''
This file contains utilities for competitions
'''
# import random
# from django.db.models import Count

from competitions.models import Competition


def get_popular_competitions(limit=4):
    '''
    Function to return most popular competitions based on the amount of participants.

    :param limit: Amount of competitions to return. Default is 3.
    :rtype: list
    :return:  Most popular competitions.
    '''

    # TODO: Fix the fetching of the popular competitions
    # Uncomment and update the following code when a long term fix is implemented for participants count

    # competitions = Competition.objects.filter(published=True) \
    #     .annotate(participant_count=Count('participants')) \
    #     .order_by('-participant_count')

    # if len(competitions) <= limit:
    #     return competitions

    # return competitions[:limit]

    # Temporary solution to show specific popular competitions
    try:
        popular_competiion_ids = [1752, 1772, 2338, 3863]
        competitions = Competition.objects.filter(id__in=popular_competiion_ids)
        return competitions
    except Exception:
        return []


def get_featured_competitions(limit=4, excluded_competitions=None):
    '''
    Function to return featured competitions if they are still open.

    :param limit: Amount of competitions to return. Default is 3
    :param excluded_competitions: list of popular competitions to prevent displaying duplicates
    :rtype: list
    :return: list of featured competitions
    '''

    # TODO: Fix the fetching of the featured competitions
    # Uncomment and update the following code when a long term fix is implemented for participants count

    # competitions = Competition.objects.filter(published=True) \
    #     .annotate(participant_count=Count('participants'))

    # if excluded_competitions:
    #     competitions = competitions.exclude(pk__in=[c.pk for c in excluded_competitions])

    # if len(competitions) <= limit:
    #     return competitions
    # else:
    #     return random.sample(list(competitions), limit)

    # Temporary solution to show specific featured competitions
    try:
        featured_competiion_ids = [3523, 2745, 3160, 1567]
        competitions = Competition.objects.filter(id__in=featured_competiion_ids)
        return competitions
    except Exception:
        return []
