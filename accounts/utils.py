from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_email(subject, template_name, context, recipients, attachments=None):
    """
    Send an HTML email using a template.

    Args:
        subject: Email subject
        template_name: Template path (e.g., 'email/welcome.html')
        context: Dict of template context variables
        recipients: List of email addresses or single email string
        attachments: Optional list of (filename, content, mimetype) tuples
    """
    if isinstance(recipients, str):
        recipients = [recipients]

    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    msg.attach_alternative(html_content, "text/html")

    if attachments:
        for filename, content, mimetype in attachments:
            msg.attach(filename, content, mimetype)

    return msg.send()
