from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

def send_email(subject, to_email, template_name, link, text_content):
    subject = subject
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [to_email]

    html_content = render_to_string(template_name, {
        "activation_link": link,
        "email": to
    })

    text_content = f"{text_content} {link}"

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending email: {e}")