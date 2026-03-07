from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import uuid

@api_view(["POST"])
def upload_model_card(request, submission_id):

    submission = Submission.objects.get(id=submission_id)

    pdf_file = request.FILES.get("model_card")

    if not pdf_file:
        return Response({"error": "No file provided"}, status=400)

    key = f"model_cards/{submission.id}/{uuid.uuid4()}.pdf"

    settings.s3_client.upload_fileobj(
        pdf_file,
        settings.S3_BUCKET,
        key,
        ExtraArgs={"ContentType": "application/pdf"},
    )

    submission.model_card_s3_key = key
    submission.model_card_status = "PENDING"
    submission.save()

    # Trigger async parser
    parse_model_card.delay(submission.id)

    return Response({"status": "uploaded"})