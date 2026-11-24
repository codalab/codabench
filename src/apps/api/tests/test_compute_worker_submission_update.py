import ast
import functools
import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest import mock

import pytest
import requests


REPO_ROOT = Path(__file__).resolve().parents[4]
HELPER_PATH = REPO_ROOT / "compute_worker" / "submission_update.py"
WORKER_PATH = REPO_ROOT / "compute_worker" / "compute_worker.py"
CONTAINERFILE_PATH = REPO_ROOT / "packaging" / "container" / "Containerfile.compute_worker"

SPEC = importlib.util.spec_from_file_location("submission_update", HELPER_PATH)
SUBMISSION_UPDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUBMISSION_UPDATE)
patch_submission = SUBMISSION_UPDATE.patch_submission
request_with_retry = SUBMISSION_UPDATE.request_with_retry


class FakeResponse:
    def __init__(self, status_code, content=b""):
        self.status_code = status_code
        self.content = content
        self.text = content.decode()


class FakeSession:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def patch(self, url, data, timeout):
        self.calls.append((url, data.copy(), timeout))
        return self._next_outcome()

    def post(self, url, json, timeout):
        self.calls.append((url, json, timeout))
        return self._next_outcome()

    def _next_outcome(self):
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


def _submission_status_values():
    tree = ast.parse(WORKER_PATH.read_text())
    status_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SubmissionStatus"
    )
    values = {}
    for node in status_class.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Name)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            values[target.id] = node.value.value
    return values


def test_retry_policy_excludes_scoring_side_effect():
    values = _submission_status_values()

    expected = {
        values["PREPARING"],
        values["RUNNING"],
        values["AWAITING_VALIDATION"],
        values["FINISHED"],
        values["FAILED"],
    }
    assert SUBMISSION_UPDATE.RETRYABLE_SUBMISSION_STATUSES == expected
    assert not SUBMISSION_UPDATE.should_retry_submission_status(
        values["SCORING"]
    )


def test_worker_uses_dedicated_no_retry_transport_for_status_retries():
    source = WORKER_PATH.read_text()

    assert "self.status_requests_session = requests.Session()" in source
    assert "status_adapter = requests.adapters.HTTPAdapter(max_retries=0)" in source
    assert (
        "session = self.status_requests_session if retry else self.requests_session"
        in source
    )
    assert "retry=should_retry_submission_status(status)" in source.replace(
        "\n", " "
    ).replace("  ", " ")


def test_compute_worker_image_includes_retry_helper():
    containerfile = CONTAINERFILE_PATH.read_text()

    assert "compute_worker/submission_update.py" in containerfile


# ---------------------------------------------------------------------------
# Generic retry helper used for the score upload POST
# ---------------------------------------------------------------------------
def call_post_retry(session, delays):
    return request_with_retry(
        session,
        "POST",
        "https://example.test/api/upload_submission_scores/42/",
        json={"secret": "s", "scores": {"score": 1}},
        timeout=(10, 150),
        retry=True,
        sleep=delays.append,
    )


def test_post_retries_server_error_until_success():
    session = FakeSession([FakeResponse(503), FakeResponse(200)])
    delays = []

    response = call_post_retry(session, delays)

    assert response.status_code == 200
    assert len(session.calls) == 2
    assert delays == [1]
    assert session.calls[0][2] == (10, 150)


def test_post_backoff_doubles_between_attempts():
    session = FakeSession([FakeResponse(503), FakeResponse(503), FakeResponse(200)])
    delays = []

    response = call_post_retry(session, delays)

    assert response.status_code == 200
    assert len(session.calls) == 3
    assert delays == [1, 2]


def test_post_retries_connection_error():
    session = FakeSession([requests.ConnectionError("temporary"), FakeResponse(200)])
    delays = []

    response = call_post_retry(session, delays)

    assert response.status_code == 200
    assert len(session.calls) == 2
    assert delays == [1]


def test_post_returns_client_error_immediately():
    session = FakeSession([FakeResponse(400), FakeResponse(200)])
    delays = []

    response = call_post_retry(session, delays)

    assert response.status_code == 400
    assert len(session.calls) == 1
    assert delays == []


def test_post_returns_conflict_immediately():
    session = FakeSession([FakeResponse(409), FakeResponse(200)])
    delays = []

    response = call_post_retry(session, delays)

    assert response.status_code == 409
    assert len(session.calls) == 1
    assert delays == []


def test_post_raises_after_last_attempt():
    session = FakeSession([requests.ReadTimeout("slow")] * 3)
    delays = []

    with pytest.raises(requests.ReadTimeout):
        call_post_retry(session, delays)

    assert len(session.calls) == 3
    assert delays == [1, 2]


# ---------------------------------------------------------------------------
# compute_worker.py loaded with its heavy dependencies stubbed
# ---------------------------------------------------------------------------
def _stub_modules():
    """Stubs for the compute worker dependencies that the API container does not need."""
    def module(name, **attrs):
        mod = types.ModuleType(name)
        mod.__dict__.update(attrs)
        return mod

    signals = types.SimpleNamespace(setup_logging=types.SimpleNamespace(connect=lambda func: func))
    billiard_exceptions = module(
        "billiard.exceptions",
        SoftTimeLimitExceeded=type("SoftTimeLimitExceeded", (Exception,), {}),
    )
    rich_pretty = module("rich.pretty", pprint=mock.MagicMock())
    rich_progress = module("rich.progress", Progress=mock.MagicMock())
    return {
        "docker": module("docker", APIClient=mock.MagicMock()),
        "websockets": module("websockets", connect=mock.MagicMock()),
        "rich": module("rich", pretty=rich_pretty, progress=rich_progress),
        "rich.pretty": rich_pretty,
        "rich.progress": rich_progress,
        "kombu": module("kombu", Queue=mock.MagicMock(), Exchange=mock.MagicMock()),
        "celery": module(
            "celery",
            Celery=mock.MagicMock(),
            shared_task=lambda *args, **kwargs: (lambda func: func),
            utils=mock.MagicMock(),
            signals=signals,
        ),
        "billiard": module("billiard", exceptions=billiard_exceptions),
        "billiard.exceptions": billiard_exceptions,
        "logs_loguru": module(
            "logs_loguru",
            configure_logging=lambda *args, **kwargs: None,
            colorize_run_args=lambda text: text,
        ),
        "submission_update": SUBMISSION_UPDATE,
    }


@functools.lru_cache(maxsize=None)
def load_compute_worker():
    stubs = _stub_modules()
    saved = {name: sys.modules.get(name) for name in stubs}
    sys.modules.update(stubs)
    try:
        spec = importlib.util.spec_from_file_location("compute_worker_under_test", WORKER_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        for name, original in saved.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
    return module


def make_mock_run(*, is_scoring, human_in_the_loop=False, **method_errors):
    run = mock.Mock()
    run.is_scoring = is_scoring
    run.human_in_the_loop = human_in_the_loop
    run.pending_detailed_results = None
    run.submission_id = 42
    run.wait_for_human_validation.return_value = True
    for method_name, error in method_errors.items():
        getattr(run, method_name).side_effect = error
    return run


def run_wrapper_with(cw, run):
    with mock.patch.object(cw, "Run", return_value=run):
        cw.run_wrapper({"secret": "00000000-0000-0000-0000-000000000000", "id": 42})


def call_sequence(run):
    """Method calls on the run in order, with status updates shown as ('_update_status', status)."""
    sequence = []
    for name, args, _ in run.mock_calls:
        if name == "_update_status":
            sequence.append((name, args[0]))
        elif "." not in name:
            sequence.append(name)
    return sequence


def statuses_sent(run):
    return [step[1] for step in call_sequence(run) if isinstance(step, tuple)]


def test_scoring_run_sends_finished_after_output_and_scores_are_uploaded():
    """The scores go last: uploading them puts the submission on the leaderboard."""
    cw = load_compute_worker()
    run = make_mock_run(is_scoring=True)

    run_wrapper_with(cw, run)

    sequence = call_sequence(run)
    finished = ("_update_status", cw.SubmissionStatus.FINISHED)
    assert sequence[:6] == [
        "validate_hitl_configuration",
        "prepare",
        "start",
        "push_output",
        "push_scores",
        finished,
    ]
    assert statuses_sent(run) == [cw.SubmissionStatus.FINISHED]


def test_hitl_scoring_run_sends_finished_after_validation_and_uploads():
    cw = load_compute_worker()
    run = make_mock_run(is_scoring=True, human_in_the_loop=True)

    run_wrapper_with(cw, run)

    assert call_sequence(run)[:8] == [
        "validate_hitl_configuration",
        "prepare",
        "start",
        ("_update_status", cw.SubmissionStatus.AWAITING_VALIDATION),
        "wait_for_human_validation",
        "push_output",
        "push_scores",
        ("_update_status", cw.SubmissionStatus.FINISHED),
    ]


def test_hitl_sends_pending_detailed_results_after_approval_before_uploads():
    cw = load_compute_worker()
    run = make_mock_run(is_scoring=True, human_in_the_loop=True)
    run.pending_detailed_results = "/tmp/detailed_results.html"
    run.send_detailed_results = mock.AsyncMock()

    run_wrapper_with(cw, run)

    run.send_detailed_results.assert_awaited_once_with("/tmp/detailed_results.html")
    sequence = call_sequence(run)
    assert sequence.index("wait_for_human_validation") < sequence.index("send_detailed_results")
    assert sequence.index("send_detailed_results") < sequence.index("push_output")
    assert sequence.index("push_output") < sequence.index("push_scores")
    assert statuses_sent(run) == [
        cw.SubmissionStatus.AWAITING_VALIDATION,
        cw.SubmissionStatus.FINISHED,
    ]


def test_hitl_rejection_marks_submission_failed_without_uploading_scores():
    cw = load_compute_worker()
    run = make_mock_run(is_scoring=True, human_in_the_loop=True)
    run.wait_for_human_validation.return_value = False

    with pytest.raises(cw.SubmissionException, match="rejected"):
        run_wrapper_with(cw, run)

    assert statuses_sent(run) == [
        cw.SubmissionStatus.AWAITING_VALIDATION,
        cw.SubmissionStatus.FAILED,
    ]
    run.push_scores.assert_not_called()
    run.push_output.assert_not_called()


def test_hitl_failed_score_upload_after_approval_marks_submission_failed():
    cw = load_compute_worker()
    run = make_mock_run(
        is_scoring=True,
        human_in_the_loop=True,
        push_scores=cw.SubmissionException("Failed to upload scores"),
    )

    with pytest.raises(cw.SubmissionException):
        run_wrapper_with(cw, run)

    assert statuses_sent(run) == [
        cw.SubmissionStatus.AWAITING_VALIDATION,
        cw.SubmissionStatus.FAILED,
    ]


def test_failed_score_upload_marks_submission_failed_never_finished():
    cw = load_compute_worker()
    run = make_mock_run(
        is_scoring=True, push_scores=cw.SubmissionException("Failed to upload scores")
    )

    with pytest.raises(cw.SubmissionException):
        run_wrapper_with(cw, run)

    assert statuses_sent(run) == [cw.SubmissionStatus.FAILED]
    run.push_output.assert_called_once()


def test_failed_output_upload_marks_scoring_run_failed_and_never_uploads_scores():
    """A Failed submission must not end up ranked, so the scores are not uploaded."""
    cw = load_compute_worker()
    run = make_mock_run(is_scoring=True, push_output=requests.ConnectionError("down"))

    with pytest.raises(requests.ConnectionError):
        run_wrapper_with(cw, run)

    assert statuses_sent(run) == [cw.SubmissionStatus.FAILED]
    run.push_scores.assert_not_called()


def test_prediction_run_sends_scoring_after_predictions_are_uploaded():
    cw = load_compute_worker()
    run = make_mock_run(is_scoring=False)

    run_wrapper_with(cw, run)

    assert call_sequence(run)[:5] == [
        "validate_hitl_configuration",
        "prepare",
        "start",
        "push_output",
        ("_update_status", cw.SubmissionStatus.SCORING),
    ]
    assert statuses_sent(run) == [cw.SubmissionStatus.SCORING]
    run.push_scores.assert_not_called()


def test_failed_prediction_upload_never_sends_scoring():
    cw = load_compute_worker()
    run = make_mock_run(is_scoring=False, push_output=requests.ConnectionError("down"))

    with pytest.raises(requests.ConnectionError):
        run_wrapper_with(cw, run)

    assert statuses_sent(run) == [cw.SubmissionStatus.FAILED]


def test_lost_scoring_update_marks_prediction_run_failed():
    cw = load_compute_worker()
    run = make_mock_run(is_scoring=False)

    def update_status(status, extra_information=None):
        if status == cw.SubmissionStatus.SCORING:
            raise cw.SubmissionException("Failure updating submission data.")

    run._update_status.side_effect = update_status

    with pytest.raises(cw.SubmissionException):
        run_wrapper_with(cw, run)

    assert statuses_sent(run) == [
        cw.SubmissionStatus.SCORING,
        cw.SubmissionStatus.FAILED,
    ]


def test_run_start_does_not_send_finished_or_scoring():
    """Run.start() itself runs containers, so check its source: the status
    transitions that trigger server-side effects now belong to run_wrapper."""
    tree = ast.parse(WORKER_PATH.read_text())
    run_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Run")
    start = next(n for n in run_class.body if isinstance(n, ast.FunctionDef) and n.name == "start")

    sent = {
        call.args[0].attr
        for call in ast.walk(start)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "_update_status"
        and call.args
        and isinstance(call.args[0], ast.Attribute)
    }
    assert "FINISHED" not in sent
    assert "SCORING" not in sent


# ---------------------------------------------------------------------------
# Run._update_status
# ---------------------------------------------------------------------------
def make_status_run(cw, *, requests_outcomes=(), status_outcomes=()):
    run = cw.Run.__new__(cw.Run)
    run.submissions_api_url = "https://example.test/api"
    run.submission_id = 42
    run.secret = "00000000-0000-0000-0000-000000000000"
    run.requests_session = FakeSession(requests_outcomes)
    run.status_requests_session = FakeSession(status_outcomes)
    return run


def test_scoring_update_error_is_raised_and_not_retried():
    cw = load_compute_worker()
    run = make_status_run(cw, requests_outcomes=[FakeResponse(502), FakeResponse(200)])

    with pytest.raises(cw.SubmissionException):
        run._update_status(cw.SubmissionStatus.SCORING)

    assert len(run.requests_session.calls) == 1
    assert run.status_requests_session.calls == []


def test_non_terminal_status_update_client_error_is_still_ignored():
    cw = load_compute_worker()
    run = make_status_run(cw, status_outcomes=[FakeResponse(400), FakeResponse(200)])

    run._update_status(cw.SubmissionStatus.PREPARING)

    assert len(run.status_requests_session.calls) == 1


# ---------------------------------------------------------------------------
# Run.push_scores
# ---------------------------------------------------------------------------
def make_scoring_run(cw, tmp_path, outcomes):
    (tmp_path / "scores.json").write_text(json.dumps({"score": 0.5}))
    run = cw.Run.__new__(cw.Run)
    run.output_dir = str(tmp_path)
    run.submissions_api_url = "https://example.test/api"
    run.submission_id = 42
    run.secret = "00000000-0000-0000-0000-000000000000"
    run.status_requests_session = FakeSession(outcomes)
    return run


@pytest.fixture
def no_retry_sleep(monkeypatch):
    cw = load_compute_worker()
    delays = []
    monkeypatch.setattr(
        cw,
        "request_with_retry",
        functools.partial(SUBMISSION_UPDATE.request_with_retry, sleep=delays.append),
    )
    return delays


def test_push_scores_succeeds_on_2xx(tmp_path, no_retry_sleep):
    cw = load_compute_worker()
    run = make_scoring_run(cw, tmp_path, [FakeResponse(201)])

    run.push_scores()

    url, payload, timeout = run.status_requests_session.calls[0]
    assert url == "https://example.test/api/upload_submission_scores/42/"
    assert payload == {"secret": run.secret, "scores": {"score": 0.5}}
    assert timeout == (10, 150)


def test_push_scores_treats_conflict_after_timeout_as_success(tmp_path, no_retry_sleep):
    """A POST that timed out after the server stored the scores is retried and gets 409."""
    cw = load_compute_worker()
    run = make_scoring_run(cw, tmp_path, [requests.ReadTimeout("slow"), FakeResponse(409)])

    run.push_scores()

    assert len(run.status_requests_session.calls) == 2
    assert no_retry_sleep == [1]


def test_push_scores_raises_on_client_error(tmp_path, no_retry_sleep):
    cw = load_compute_worker()
    run = make_scoring_run(cw, tmp_path, [FakeResponse(400, b"bad scores" + b"x" * 1000)])

    with pytest.raises(cw.SubmissionException) as excinfo:
        run.push_scores()

    message = str(excinfo.value)
    assert "status=400" in message
    assert "bad scores" in message
    assert len(message) < 600
    assert len(run.status_requests_session.calls) == 1


def test_push_scores_raises_after_exhausting_retries(tmp_path, no_retry_sleep):
    cw = load_compute_worker()
    run = make_scoring_run(cw, tmp_path, [requests.ConnectionError("down")] * 3)

    with pytest.raises(cw.SubmissionException) as excinfo:
        run.push_scores()

    assert isinstance(excinfo.value.__cause__, requests.ConnectionError)
    assert no_retry_sleep == [1, 2]


def test_push_scores_raises_on_persistent_server_error(tmp_path, no_retry_sleep):
    cw = load_compute_worker()
    run = make_scoring_run(cw, tmp_path, [FakeResponse(503)] * 3)

    with pytest.raises(cw.SubmissionException, match="status=503"):
        run.push_scores()

    assert len(run.status_requests_session.calls) == 3


# ---------------------------------------------------------------------------
# Transport retries of the general session
# ---------------------------------------------------------------------------
def make_real_run(cw, tmp_path, monkeypatch):
    monkeypatch.setattr(cw.Settings, "BASE_DIR", f"{tmp_path}/")
    run_args = {
        "user_pk": 1,
        "id": 42,
        "is_scoring": False,
        "submissions_api_url": "https://example.test/api",
        "docker_image": "codalab/codalab-legacy:py37",
        "secret": "00000000-0000-0000-0000-000000000000",
        "prediction_result": "https://example.test/prediction",
        "execution_time_limit": 60,
        "prediction_stdout": "",
        "prediction_stderr": "",
        "prediction_ingestion_stdout": "",
        "prediction_ingestion_stderr": "",
    }
    return cw.Run(run_args)


def test_general_session_does_not_retry_patch(tmp_path, monkeypatch):
    cw = load_compute_worker()
    run = make_real_run(cw, tmp_path, monkeypatch)

    retry = run.requests_session.get_adapter("https://example.test").max_retries

    assert "PATCH" not in retry.allowed_methods
    assert {"GET", "PUT"} <= set(retry.allowed_methods)
    assert retry.connect is None or retry.connect > 0
    assert retry.total == 3


def test_status_session_has_no_transport_retries(tmp_path, monkeypatch):
    cw = load_compute_worker()
    run = make_real_run(cw, tmp_path, monkeypatch)

    retry = run.status_requests_session.get_adapter("https://example.test").max_retries

    assert retry.total == 0


def test_secret_is_masked_in_logged_payload():
    cw = load_compute_worker()

    masked = cw.mask_secret({"secret": "top-secret", "status": "Running"})

    assert masked == {"secret": "********", "status": "Running"}
