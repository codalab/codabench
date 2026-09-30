import ast
import importlib.util
from pathlib import Path

import requests


REPO_ROOT = Path(__file__).resolve().parents[4]
HELPER_PATH = REPO_ROOT / "compute_worker" / "submission_update.py"
WORKER_PATH = REPO_ROOT / "compute_worker" / "compute_worker.py"

SPEC = importlib.util.spec_from_file_location("submission_update", HELPER_PATH)
SUBMISSION_UPDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUBMISSION_UPDATE)
patch_submission = SUBMISSION_UPDATE.patch_submission


class FakeResponse:
    def __init__(self, status_code, content=b""):
        self.status_code = status_code
        self.content = content


class FakeSession:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def patch(self, url, data, timeout):
        self.calls.append((url, data.copy(), timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def call_retry(session, delays, **overrides):
    kwargs = {
        "timeout": 150,
        "retry": True,
        "sleep": delays.append,
    }
    kwargs.update(overrides)
    return patch_submission(
        session,
        "https://example.test/api/submissions/42/",
        {"status": "Preparing"},
        **kwargs,
    )


def test_retries_transient_server_errors_until_success():
    session = FakeSession(
        [FakeResponse(500), FakeResponse(503), FakeResponse(200)]
    )
    delays = []

    response = call_retry(session, delays)

    assert response.status_code == 200
    assert len(session.calls) == 3
    assert delays == [1, 2]


def test_does_not_retry_non_retryable_client_error():
    session = FakeSession([FakeResponse(400), FakeResponse(200)])
    delays = []

    response = call_retry(session, delays)

    assert response.status_code == 400
    assert len(session.calls) == 1
    assert delays == []


def test_retries_request_exception():
    session = FakeSession(
        [requests.ConnectionError("temporary"), FakeResponse(200)]
    )
    delays = []

    response = call_retry(session, delays)

    assert response.status_code == 200
    assert len(session.calls) == 2
    assert delays == [1]


def test_retry_is_opt_in_for_non_idempotent_submission_updates():
    session = FakeSession([FakeResponse(500), FakeResponse(200)])
    delays = []

    response = patch_submission(
        session,
        "https://example.test/api/submissions/42/",
        {"type": "Docker_Image_Pull_Fail"},
        timeout=150,
        retry=False,
        sleep=delays.append,
    )

    assert response.status_code == 500
    assert len(session.calls) == 1
    assert delays == []


def test_retries_rate_limit_response():
    session = FakeSession([FakeResponse(429), FakeResponse(200)])
    delays = []

    response = call_retry(session, delays)

    assert response.status_code == 200
    assert len(session.calls) == 2
    assert delays == [1]


def test_only_status_updates_opt_in_to_retry():
    tree = ast.parse(WORKER_PATH.read_text())
    retrying_callers = []
    direct_callers = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if not isinstance(child.func, ast.Attribute):
                continue
            if child.func.attr != "_update_submission":
                continue

            retry_keyword = next(
                (kw for kw in child.keywords if kw.arg == "retry"),
                None,
            )
            if (
                retry_keyword is not None
                and isinstance(retry_keyword.value, ast.Constant)
                and retry_keyword.value.value is True
            ):
                retrying_callers.append(node.name)
            else:
                direct_callers.append(node.name)

    assert retrying_callers == ["_update_status"]
    assert direct_callers
