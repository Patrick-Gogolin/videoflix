from rest_framework import serializers
from ..models import Video

class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for the Video model.

    Fields:
        id (int): Unique identifier of the video.
        created_at (datetime): Creation date of the video.
        title (str): Title of the video.
        description (str): Description of the video.
        thumbnail_url (str): Absolute URL of the video's thumbnail.
        category (str): Category of the video.

    Methods:
        get_thumbnail_url(obj): Returns the absolute URL of the thumbnail if it exists.
    """
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None