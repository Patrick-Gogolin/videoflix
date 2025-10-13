from django.urls import path
from .views import VideoListAPIView

urlpatterns = [
    path('videos/', VideoListAPIView.as_view(), name='video-list'),
]