from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
import logging

logger = logging.getLogger(__name__)

def send_email(subject, recipient, template_name, link, text_content):
    subject = subject
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [recipient]

    html_content = render_to_string(template_name, {
        "link": link,
        "email": recipient
    })

    body_text = f"{text_content} {link}"

    msg = EmailMultiAlternatives(subject, body_text, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        logger.error(f"Error sending email to {to}: {e}")