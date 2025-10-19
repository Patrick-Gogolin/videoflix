from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
import logging

logger = logging.getLogger(__name__)

def send_email(subject, recipient, template_name, link, text_content):
    """
    Sends an email with both plain text and HTML content.

    Args:
        subject (str): The email subject line.
        recipient (str): Recipient email address.
        template_name (str): Path to the HTML email template.
        link (str): URL to include in the email (e.g., activation or reset link).
        text_content (str): Plain text content to include in the email body.

    Process:
        1. Renders the HTML template with the recipient and link.
        2. Constructs a plain text version of the email.
        3. Creates an EmailMultiAlternatives object with both HTML and plain text.
        4. Attempts to send the email, logging any errors if sending fails.
    """
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