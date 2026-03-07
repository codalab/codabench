from django.conf import settings

def get_model_card_url(submission):

    if submission.competition.model_card_visibility != "public":
        return None

    url = settings.s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": submission.model_card_s3_key,
        },
        ExpiresIn=3600,
    )

    return url