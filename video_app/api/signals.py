from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import Video
import django_rq
from video_app.api.tasks import generate_thumbnail, generate_hls

@receiver(post_save, sender=Video)
def generate_thumbnail_and_hls_signal(sender, instance, created, **kwargs):
    """
    Signal handler that triggers background tasks after a Video instance is created.

    When a new Video with a file is saved, this signal enqueues:
        - `generate_thumbnail`: Creates a thumbnail for the video.
        - `generate_hls`: Generates HLS streaming files.

    Args:
        sender (Model): The model class (Video).
        instance (Video): The saved Video instance.
        created (bool): True if a new record was created.
        **kwargs: Additional keyword arguments.
    """
    if created and instance.video_file:
        queue = django_rq.get_queue("default")
        queue.enqueue(generate_thumbnail, instance.id)
        queue.enqueue(generate_hls, instance.id)