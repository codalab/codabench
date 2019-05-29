from django.core.mail import EmailMessage


def codalab_send_mail(subject, message, recipient_list):
    message = EmailMessage(
        subject=subject,
        body=message,
        to=recipient_list
    )
    message.send()
