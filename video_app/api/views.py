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

class VideoListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        videos = Video.objects.filter(hls_ready=True).order_by('-created_at')
        serializer = VideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class VideoStreamAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, movie_id, resolution):
        manifest_path = os.path.join(settings.MEDIA_ROOT, "videos", str(movie_id), resolution, "index.m3u8")
        if not os.path.exists(manifest_path):
            return Response("Video or Manifest not found", status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(manifest_path, "rb"), content_type="application/vnd.apple.mpegurl")
    
class VideoSegmentAPIView(APIView):
    """
    Gibt ein einzelnes HLS-Videosegment (.ts) für ein Video in der gewünschten Auflösung zurück.
    """
    permission_classes = [IsAuthenticated]
    def get(self, request, movie_id, resolution, segment):
        segment_path = os.path.join(settings.MEDIA_ROOT, "videos", str(movie_id), resolution, segment)

        if not os.path.exists(segment_path):
            return Response("Video or Segment not found", status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(segment_path, "rb"), content_type="video/MP2T")