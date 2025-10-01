from django.dispatch import receiver
import django_rq
from rq import Retry
from .signals import user_registered, password_reset_requested
from .tasks import send_activation_email_task, send_password_reset_email

@receiver(user_registered)
def enqueue_activation_email(sender, user, **kwargs):
    queue = django_rq.get_queue('default')
    queue.enqueue(send_activation_email_task, user.pk, user.email, retry=Retry(max=3,interval=[10,30,60]))

@receiver(password_reset_requested)
def enqueue_password_reset_email(sender, user, **kwargs):
    queue = django_rq.get_queue('default')
    queue.enqueue(send_password_reset_email, user.pk, user.email, retry=Retry(max=3,interval=[10,30,60]))