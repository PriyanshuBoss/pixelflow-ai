import requests
from PIL import Image, ImageDraw, ImageFont
import io
import math

def create_tiled_watermark(image, watermark_text, opacity=175, color='#f8f8ff', style='normal'):
    """
    Create a diagonal watermark across the image from bottom-left to top-right
    
    Args:
        image: PIL Image object
        watermark_text: Text to use as watermark
        opacity: Transparency level (0-255, lower is more transparent)
        color: Hex color code for the watermark
        style: 'normal' or 'confidential' (adds border and background)
    """

    color = color.lstrip('#')
    r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
   
    overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Larger font for single diagonal watermark
    font_size = int(min(image.width, image.height) * 0.08)
    
    font_path = "/var/task/common/arial.ttf"

    try:
        font = ImageFont.truetype(f"{font_path}", font_size)
        print(f"{font = }")
    except Exception as e:
        print(f"⚠️ Could not load {font_path}: {e}")
        font = ImageFont.load_default()

    
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate diagonal angle from bottom-left to top-right
    # Positive angle to rotate counter-clockwise
    rotation_angle = math.degrees(math.atan2(image.height, image.width))
    
    # Create a canvas large enough for rotated text
    diagonal_length = int(math.sqrt(image.width**2 + image.height**2))
    
    canvas_size = diagonal_length
    text_layer = Image.new('RGBA', (canvas_size, canvas_size), (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_layer)
    text_position = ((canvas_size - text_width) // 2, (canvas_size - text_height) // 2)
    text_draw.text(text_position, watermark_text, 
                       fill=(r, g, b, opacity), font=font)
        
    
    rotated_text = text_layer.rotate(rotation_angle, expand=False)
    
    # Center the rotated text on the image
    x_offset = (image.width - rotated_text.width) // 2
    y_offset = (image.height - rotated_text.height) // 2
    
    overlay.paste(rotated_text, (x_offset, y_offset), rotated_text)
    
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    watermarked = Image.alpha_composite(image, overlay)
    
    return watermarked


def watermark_from_url(image_url, watermark_text='GAANA-AI'):
    """
    Download image from S3 URL, add watermark, and return the PIL image
    
    Args:
        image_url: S3 URL or any image URL
        watermark_text: Text to use as watermark
    Returns:
        watermarked PIL.Image object or False on error
    """
    try:
        print(f"[INFO] Starting download from: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        print(f"[INFO] Download successful. Status code: {response.status_code}")

        # Open image
        image = Image.open(io.BytesIO(response.content))
        print(f"[INFO] Image opened successfully. Format: {image.format}, Size: {image.size}, Mode: {image.mode}")

        # Add watermark
        print(f"[INFO] Adding watermark: '{watermark_text}'")
        watermarked_image = create_tiled_watermark(image, watermark_text)
        print(f"[INFO] Watermark added successfully.")

        return watermarked_image

    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout while trying to download image from {image_url}")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error while downloading image: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request exception: {e}")
        return False
    except IOError as e:
        print(f"[ERROR] IOError while opening image: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False
