from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from video_app.models import Video
from .serializers import VideoSerializer
from rest_framework.permissions import IsAuthenticated

class VideoListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        videos = Video.objects.all().order_by('-created_at')
        serializer = VideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)