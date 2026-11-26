class PartialFetchError(Exception):
    """
    Raised by a fetcher that made some progress (e.g. fetched earlier pages of a
    paginated response) before hitting an error. Carries whatever papers were
    already collected, so sync_citing_papers can save that partial result instead
    of discarding it entirely.
    """

    def __init__(self, papers, original_exception):
        self.papers = papers
        self.original_exception = original_exception
        super().__init__(str(original_exception))
