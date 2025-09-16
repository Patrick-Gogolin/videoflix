from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model


def send_activation_email_task(user_id, email):
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    
    activation_link = f"http://127.0.0.1:5500/pages/auth/activate.html?uid={uidb64}&token={token}"

    subject = "Confirm your email"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email]

    html_content = render_to_string("emails/activation_email.html", {
        "activation_link": activation_link,
        "email": email
    })

    text_content = f"Please activate your account: {activation_link}"

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending email: {e}")


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