from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonBurstRateThrottle(AnonRateThrottle):
    scope = 'anon_burst'


class UserBurstRateThrottle(UserRateThrottle):
    scope = 'user_burst'
