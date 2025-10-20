import os
import subprocess
import logging
from django.conf import settings
from ..models import Video

logger = logging.getLogger(__name__)

def generate_thumbnail(video_id):
    """
    Generates a thumbnail for the given Video instance.

    Uses ffmpeg to capture a frame at 5 seconds and saves it as a JPEG
    in MEDIA_ROOT/thumbnails/. Updates the Video instance's `thumbnail` field.

    Args:
        video_id (int): ID of the Video instance.
    """
    try:
        video = Video.objects.get(id=video_id)
        input_path = video.video_file.path

        output_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(output_dir, exist_ok=True)

        filename = os.path.splitext(os.path.basename(input_path))[0] + ".jpg"
        output_path = os.path.join(output_dir, filename)

        cmd = [
            "ffmpeg",
            "-y",              
            "-i", input_path,   
            "-ss", "00:00:05", 
            "-vframes", "1",    
            output_path,        
        ]
        subprocess.run(cmd, check=True)

        video.thumbnail.name = f"thumbnails/{filename}"  
        video.save(update_fields=["thumbnail"])  

        logger.info("✅ Thumbnail erstellt Video %s erstellt unter %s", video.id, output_path)
    
    except Exception as e:
        logger.exception("❌ Fehler bei Thumbnail-Erstellung für Video: %s: %s", video_id, e)


def generate_hls(video_id):
    """
    Generates HLS streaming files for the given Video instance.

    Uses ffmpeg to create HLS playlists in multiple resolutions
    (480p, 720p, 1080p) and saves them under MEDIA_ROOT/videos/<video_id>/. 
    Updates the Video instance's `hls_ready` field upon success.

    Args:
        video_id (int): ID of the Video instance.
    """
    try:
        video = Video.objects.get(id=video_id)
        input_path = video.video_file.path

        base_output_dir = os.path.join(settings.MEDIA_ROOT, "videos", str(video.id))
        os.makedirs(base_output_dir, exist_ok=True)

        resolutions = {
            "480p": "854:480",
            "720p": "1280:720",
            "1080p": "1920:1080"
        }

        for label, size in resolutions.items():
            output_dir = os.path.join(base_output_dir, label)
            os.makedirs(output_dir, exist_ok=True)
        
            cmd = [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-vf", f"scale={size}",
                "-c:v", "h264",
                "-c:a", "aac",
                "-hls_time", "5", 
                "-hls_playlist_type", "vod",
                os.path.join(output_dir, "index.m3u8")
            ]
            subprocess.run(cmd, check=True)

        video.hls_ready = True
        video.save(update_fields=["hls_ready"])
        
        logger.info("✅ HLS-Dateien für Video %s erstellt unter %s", video.id, base_output_dir)

    except Exception as e:
         logger.exception("❌ Fehler bei HLS-Erstellung für Video %s: %s", video_id, e)