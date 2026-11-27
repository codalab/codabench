import nh3
import markdown
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def get_link_context(request=None):
    """
    Build the {domain, protocol} pair used for absolute links in email templates.

    Pass `request` when one is available so the scheme matches how the user
    actually connected (relevant behind a reverse proxy terminating TLS).
    Omit it (e.g. from a model method with no request in scope) and it
    defaults to 'https', since production is HTTPS-only.
    """
    return {
        'domain': settings.DOMAIN_NAME,
        'protocol': 'https' if request is None or request.is_secure() else 'http',
    }


def codalab_send_mail(context_data, to_email, html_file, text_file, subject, from_email=None):
    from_email = from_email if from_email else settings.DEFAULT_FROM_EMAIL

    context_data["site"] = Site.objects.get_current()

    text = render_to_string(text_file, context_data)
    html = render_to_string(html_file, context_data)
    to_email = to_email if type(to_email) is list else [to_email]
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
    return nh3.clean(
        content,
        tags=tags,
        attributes=attrs
    )


def codalab_send_markdown_email(subject, markdown_content, recipient_list, from_email=None):
    from_email = from_email if from_email else settings.DEFAULT_FROM_EMAIL
    html_message = markdown.markdown(markdown_content)
    # message = sanitize(markdown_content)
    # html_message = sanitize(markdown.markdown(message))

    message = EmailMultiAlternatives(subject, '', from_email=from_email, bcc=recipient_list)
    message.attach_alternative(html_message, 'text/html')
    message.send()
