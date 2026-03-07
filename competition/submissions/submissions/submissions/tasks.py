from celery import shared_task
from django.conf import settings
from .models import Submission
import json
import tempfile
import pdfplumber


@shared_task
def parse_model_card(submission_id):

    submission = Submission.objects.get(id=submission_id)

    try:
        # Download PDF from S3
        response = settings.s3_client.get_object(
            Bucket=settings.S3_BUCKET,
            Key=submission.model_card_s3_key,
        )

        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(response["Body"].read())
            tmp.flush()

            parsed_data = extract_pdf_to_json(tmp.name)

        submission.model_card_json = parsed_data
        submission.model_card_status = "PARSED"
        submission.save()

    except Exception as e:
        submission.model_card_status = "FAILED"
        submission.model_card_error = str(e)
        submission.save()