from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, SimpleRateThrottle


class AnonBurstRateThrottle(AnonRateThrottle):
    scope = 'anon_burst'


class UserBurstRateThrottle(UserRateThrottle):
    scope = 'user_burst'


class ServiceAccountRateThrottle(UserRateThrottle):
    """
    Throttling made to rise the number of request authorized for Compute Workers
    Limit defined in settings: 'service_account': '20000/day',
    """
    scope = 'service_account'

    def allow_request(self, request, view):
        user = getattr(request, 'user', None)
        if not (user and user.is_authenticated):
            return super().allow_request(request, view)

        if user.groups.filter(name='service_accounts').exists():
            self.scope = 'service_account'
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)

        return super().allow_request(request, view)


class SubmissionOwnerRateThrottle(SimpleRateThrottle):
    """
    Throttle for Compute Workers by user, to avoid other users to use the CW if throttled by an other user
    """
    scope = 'submission_owner'

    def get_cache_key(self, request, view):
        if not (request.user and request.user.is_authenticated
                and request.user.groups.filter(name='service_accounts').exists()):
            return None

        submission_owner_id = self._extract_owner_id(request)
        if submission_owner_id is None:
            return None

        return self.cache_format % {
            'scope': self.scope,
            'ident': submission_owner_id,
        }

    def _extract_owner_id(self, request):
        return request.data.get('owner_id')
