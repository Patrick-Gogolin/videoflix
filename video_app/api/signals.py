from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import Video
import django_rq
from video_app.api.tasks import generate_thumbnail, generate_hls

@receiver(post_save, sender=Video)
def generate_thumbnail_and_hls_signal(sender, instance, created, **kwargs):
    if created and instance.video_file:
        queue = django_rq.get_queue("default")
        queue.enqueue(generate_thumbnail, instance.id)
        queue.enqueue(generate_hls, instance.id)