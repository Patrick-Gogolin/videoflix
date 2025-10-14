import os
import subprocess
from django.conf import settings
from ..models import Video

def generate_thumbnail(video_id):
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

        # Model aktualisieren
        video.thumbnail.name = f"thumbnails/{filename}"
        video.save(update_fields=["thumbnail"])

        print(f"✅ Thumbnail erstellt: {output_path}")
    
    except Exception as e:
        print(f"❌ Fehler bei Thumbnail-Erstellung: {e}")