import time

import requests


RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

# These worker status updates are safe to repeat at the application level.
# SCORING is intentionally excluded: the API serializer dispatches a scoring
# task when it receives that status, so an ambiguous response could otherwise
# launch scoring twice.
RETRYABLE_SUBMISSION_STATUSES = frozenset({
    "Preparing",
    "Running",
    "Awaiting validation",
    "Finished",
    "Failed",
})


def should_retry_submission_status(status):
    return status in RETRYABLE_SUBMISSION_STATUSES


def patch_submission(
    session,
    url,
    data,
    *,
    timeout,
    retry=False,
    max_attempts=3,
    backoff_factor=1,
    sleep=time.sleep,
):
    """PATCH submission data, optionally retrying transient failures.

    Retrying is opt-in because some submission PATCH payloads have
    non-idempotent server-side effects (for example, appending worker errors
    to stderr), and the SCORING status dispatches a new scoring task. Only
    explicitly allowlisted worker statuses use application-level retries.
    """
    attempts = max_attempts if retry else 1
    if attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    for attempt in range(1, attempts + 1):
        try:
            response = session.patch(url, data=data, timeout=timeout)
        except requests.RequestException:
            if attempt >= attempts:
                raise
        else:
            if (
                response.status_code not in RETRYABLE_STATUS_CODES
                or attempt >= attempts
            ):
                return response

        sleep(backoff_factor * (2 ** (attempt - 1)))

    raise RuntimeError("retry loop exited unexpectedly")
