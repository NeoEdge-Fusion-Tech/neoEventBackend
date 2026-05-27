import os
from celery import shared_task
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import io

@shared_task
def process_watermark_for_media(invited_media_id):
    from events.models.vendor import InvitedEventMedia
    try:
        media = InvitedEventMedia.objects.get(id=invited_media_id)
        if media.is_processed:
            return
            
        # Open the original image
        original_image = Image.open(media.raw_image.path).convert("RGBA")
        width, height = original_image.size
        
        # Create a transparent overlay
        watermark = Image.new("RGBA", original_image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        
        # Determine font size and text
        text = "PREVIEW ONLY"
        font_size = int(width / 10)
        
        try:
            # Try to load a standard font, fallback to default if not found
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
            
        # Try to use textbbox for newer Pillow versions, fallback to textsize
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            text_width, text_height = draw.textsize(text, font)
        
        # Position in center
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        # Draw text with 50% opacity white
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))
        
        # Merge watermark with original image
        watermarked_image = Image.alpha_composite(original_image, watermark).convert("RGB")
        
        # Save to a bytes buffer
        buffer = io.BytesIO()
        watermarked_image.save(buffer, format="JPEG", quality=85)
        
        # Save back to model
        file_name = f"watermarked_{os.path.basename(media.raw_image.name)}"
        media.watermarked_image.save(file_name, ContentFile(buffer.getvalue()), save=False)
        media.is_processed = True
        media.save()
        
    except Exception as e:
        print(f"Failed to process watermark: {e}")
