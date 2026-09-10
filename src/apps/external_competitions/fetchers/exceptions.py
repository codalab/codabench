class PartialFetchError(Exception):
    """
    Raised by a fetcher that made some progress (e.g. fetched earlier pages of a
    paginated response) before hitting an error. Carries whatever competitions
    were already collected, so sync_platform can save that partial result instead
    of discarding a partially-successful fetch entirely.
    """

    def __init__(self, competitions, original_exception):
        self.competitions = competitions
        self.original_exception = original_exception
        super().__init__(str(original_exception))
