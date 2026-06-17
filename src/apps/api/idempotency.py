import hashlib
import json
import logging

from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, transaction
from rest_framework import status as http
from rest_framework.response import Response

from competitions.models import IdempotencyRecord

logger = logging.getLogger(__name__)

ENDPOINT_SUBMISSION_CREATE = "submissions.create"


def _fingerprint(data):
    """Stable sha256 over the request body."""
    try:
        canonical = json.dumps(data, sort_keys=True, default=str)
    except TypeError:
        canonical = repr(data)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_safe(data):
    """Round-trip through DjangoJSONEncoder so UUID/datetime/Decimal survive."""
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


class IdempotentCreateMixin:
    """Replay-safe POST keyed by the `Idempotency-Key` header.

    Behaviour:
      * No header                       -> falls back to legacy create() (compat).
      * Header + first call             -> runs create(), stores response, returns it.
      * Header + replay, same payload   -> returns stored response (same id).
      * Header + replay, diff payload   -> 409 Conflict.
      * Header + in-flight (race)       -> 409 Conflict ("request already in flight").

    The owner of the key is `request.user`; an anonymous user gets the legacy
    path because there is no stable identity to scope the key.
    """
    idempotency_endpoint = ENDPOINT_SUBMISSION_CREATE

    def create(self, request, *args, **kwargs):
        key = request.headers.get("Idempotency-Key")
        if not key or not request.user.is_authenticated:
            return super().create(request, *args, **kwargs)

        fp = _fingerprint(request.data)
        owner = request.user
        endpoint = self.idempotency_endpoint

        try:
            with transaction.atomic():
                rec = (
                    IdempotencyRecord.objects
                    .select_for_update()
                    .filter(owner=owner, endpoint=endpoint, key=key)
                    .first()
                )
                if rec is None:
                    rec = IdempotencyRecord.objects.create(
                        owner=owner,
                        endpoint=endpoint,
                        key=key,
                        request_fingerprint=fp,
                    )
                    is_new = True
                else:
                    is_new = False
        except IntegrityError:
            rec = IdempotencyRecord.objects.get(owner=owner, endpoint=endpoint, key=key)
            is_new = False

        if not is_new:
            if rec.request_fingerprint != fp:
                return Response(
                    {"detail": "Idempotency-Key reused with a different payload"},
                    status=http.HTTP_409_CONFLICT,
                )
            if rec.response_status:
                return Response(rec.response_body, status=rec.response_status)
            return Response(
                {"detail": "Request already in flight for this Idempotency-Key"},
                status=http.HTTP_409_CONFLICT,
            )

        resp = super().create(request, *args, **kwargs)

        body = resp.data if isinstance(resp.data, (dict, list)) else {}
        rec.response_status = resp.status_code
        rec.response_body = _json_safe(body)
        if isinstance(resp.data, dict) and "id" in resp.data:
            rec.submission_id = resp.data["id"]
        rec.save(update_fields=["response_status", "response_body", "submission", "updated_when"])
        return resp
