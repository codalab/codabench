import bleach
import markdown
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def codalab_send_mail(context_data, to_email, html_file, text_file, subject, from_email=None):
    from_email = from_email if from_email else settings.SERVER_EMAIL

    context_data["site"] = Site.objects.get_current()

    text = render_to_string(text_file, context_data)
    html = render_to_string(html_file, context_data)
    to_email = to_email if type(to_email) == list else [to_email]
    message = EmailMultiAlternatives(subject, text, from_email=from_email, to=to_email)
    message.attach_alternative(html, 'text/html')
    message.send()


def sanitize(content):
    tags = [
        'img',
        'p',
        'br',
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
    ]
    attrs = {'img': ['src']}
    return bleach.clean(
        content,
        tags=tags,
        attributes=attrs
    )


def codalab_send_markdown_email(subject, markdown_content, recipient_list, from_email=None):
    from_email = from_email if from_email else settings.SERVER_EMAIL
    html_message = markdown.markdown(markdown_content)
    # message = sanitize(markdown_content)
    # html_message = sanitize(markdown.markdown(message))

    message = EmailMultiAlternatives(subject, '', from_email=from_email, bcc=recipient_list)
    message.attach_alternative(html_message, 'text/html')
    message.send()
