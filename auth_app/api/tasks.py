from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from .utils import send_email

def send_activation_email_task(user_id, user_email):
    """
    Sends an account activation email to a newly registered user.

    Args:
        user_id (int): The primary key of the user.
        user_email (str): Recipient email address.

    Process:
        1. Retrieves the user by ID.
        2. Generates a one-time activation token.
        3. Encodes the user ID safely for URL usage.
        4. Constructs an activation link.
        5. Sends an email with the activation link using a template.
    """
    user = User.objects.get(pk=user_id)
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    
    activation_link = f"http://127.0.0.1:5500/pages/auth/activate.html?uid={uidb64}&token={token}"
    
    send_email(subject="Confirm your email",
                recipient=user_email,
                template_name="emails/activation_email.html",
                link=activation_link,
                text_content="Click the link to activate your account:")

def send_password_reset_email(user_id, user_email):
    """
    Sends a password reset email to a user who requested it.

    Args:
        user_id (int): The primary key of the user.
        user_email (str): Recipient email address.

    Process:
        1. Retrieves the user by ID.
        2. Generates a one-time password reset token.
        3. Encodes the user ID safely for URL usage.
        4. Constructs a password reset link.
        5. Sends an email with the reset link using a template.
    """
    user = User.objects.get(pk=user_id)
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
   
    reset_url = f"http://127.0.0.1:5500/pages/auth/confirm_password.html?uid={uidb64}&token={token}"

    send_email(subject="Reset your Password",
                recipient=user_email,
                template_name="emails/password_reset_email.html",
                link=reset_url,
                text_content="Click the link to reset your password:")