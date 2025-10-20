from django.db import models

# Create your models here.

class Video(models.Model):
    """
    Represents a video uploaded to the platform.

    Fields:
        title (str): Title of the video.
        description (str): Description of the video content.
        video_file (File): Uploaded video file.
        thumbnail (File, optional): Thumbnail image for the video.
        category (str): Video category. Choices are Drama, Romance, Action, Comedy, Documentary.
        created_at (datetime): Timestamp when the video was created.
        hls_ready (bool): Indicates if HLS streaming files have been generated.

    Methods:
        __str__(): Returns a string representation of the video including title and primary key.
    """
    CATEGORY_CHOICES = [
        ('Drama', 'Drama'),
        ('Romance', 'Romance'),
        ('Action', 'Action'),
        ('Comedy', 'Comedy'),
        ('Documentary', 'Documentary'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    video_file = models.FileField(upload_to='videos/')
    thumbnail = models.FileField(upload_to='thumbnails/', null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    hls_ready = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} {self.pk}"