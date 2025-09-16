from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .signals import user_registered, password_reset_requested


@receiver(user_registered)
def send_activation_email(sender, user, **kwargs):
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    
    activation_link = f"http://127.0.0.1:5500/pages/auth/activate.html?uid={uidb64}&token={token}"

    subject = "Confirm your email"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    html_content = render_to_string("emails/activation_email.html", {
        "activation_link": activation_link,
        "email": user.email
    })

    text_content = f"Please activate your account: {activation_link}"

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending email: {e}")

@receiver(password_reset_requested)
def send_password_reset_email(sender, user, token, uidb64, **kwargs):
   reset_url = f"http://127.0.0.1:5500/pages/auth/confirm_password.html?uid={uidb64}&token={token}"

   subject = "Reset your Password"
   from_email = settings.DEFAULT_FROM_EMAIL
   to = [user.email]
   
   html_content = render_to_string("emails/password_reset_email.html", {
            "activation_link": reset_url,
            "email": user.email
        })

   text_content = f"Please activate your account using the link: {reset_url}"

   msg = EmailMultiAlternatives(subject, text_content, from_email, to)
   msg.attach_alternative(html_content, "text/html")

   try:
        msg.send(fail_silently=False)
   except Exception as e:
        print(f"Error sending email: {e}")