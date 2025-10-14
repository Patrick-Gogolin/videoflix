from django.db import models
import django_rq

# Create your models here.

class Video(models.Model):
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

    def __str__(self):
        return self.title