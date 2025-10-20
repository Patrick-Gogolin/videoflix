from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from video_app.models import Video
from .serializers import VideoSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

class VideoListAPIView(APIView):
    """
    API view that returns a list of all HLS-ready videos.

    Permissions:
        - Only authenticated users can access this view.

    Methods:
        get(request): Returns serialized list of videos ordered by creation date.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            videos = Video.objects.filter(hls_ready=True).order_by('-created_at')
            serializer = VideoSerializer(videos, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error fetching video list: %s", e)
            return Response(
                {"detail": "An error occurred while fetching videos."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VideoStreamAPIView(APIView):
    """
    API view that serves the HLS manifest (.m3u8) for a specific video.

    Permissions:
        - Only authenticated users can access this view.

    Methods:
        get(request, movie_id, resolution): Returns the HLS manifest file for the video in the requested resolution.
    """
    permission_classes = [IsAuthenticated]
    def get(self, request, movie_id, resolution):
        manifest_path = os.path.join(settings.MEDIA_ROOT, "videos", str(movie_id), resolution, "index.m3u8")
        if not os.path.exists(manifest_path):
            return Response("Video or Manifest not found", status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(manifest_path, "rb"), content_type="application/vnd.apple.mpegurl")
    
class VideoSegmentAPIView(APIView):
    """
    API view that serves individual HLS video segments (.ts) for a video.

    Permissions:
        - Only authenticated users can access this view.

    Methods:
        get(request, movie_id, resolution, segment): Returns the requested video segment in the specified resolution.
    """
    permission_classes = [IsAuthenticated]
    def get(self, request, movie_id, resolution, segment):
        segment_path = os.path.join(settings.MEDIA_ROOT, "videos", str(movie_id), resolution, segment)

        if not os.path.exists(segment_path):
            return Response("Video or Segment not found", status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(segment_path, "rb"), content_type="video/MP2T")