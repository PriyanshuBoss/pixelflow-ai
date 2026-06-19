import base64
import io
import requests
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict

from PIL import Image, ImageFile

SLACK_API_KEY = os.getenv('SLACK_API_KEY')
ENVIRONMENT = os.getenv('ENVIRONMENT', "staging")


# Custom Exception Classes
class ImageEnhancementError(Exception):
    """Base exception for image enhancement operations"""

    pass


class APIConnectionError(ImageEnhancementError):
    """Raised when API connection fails"""

    pass


class InvalidImageError(ImageEnhancementError):
    """Raised when image file is invalid or unsupported"""

    pass


class ConfigurationError(ImageEnhancementError):
    """Raised when configuration is missing or invalid"""

    pass


# Logging Setup
def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Configure and return a logger instance with consistent formatting"""
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper()))

    return logger


# Input Validation Functions
def validate_image_file(image_path: str) -> None:
    """Validate that image file exists and is in supported format"""
    if not os.path.isfile(image_path):
        raise InvalidImageError(f"Image file not found: {image_path}")

    supported_formats = {".jpg", ".jpeg", ".png"}
    file_extension = Path(image_path).suffix.lower()

    if file_extension not in supported_formats:
        raise InvalidImageError(
            f"Unsupported image format: {file_extension}. "
            f"Supported formats: {', '.join(supported_formats)}"
        )


def validate_prompt(prompt: str) -> None:
    """Validate that prompt is not empty and within reasonable limits"""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")


def validate_iterations(iterations: int) -> None:
    """Validate iteration count is within reasonable bounds"""
    if iterations < 1:
        raise ValueError("Iterations must be at least 1")

def check_and_change_image_aspect_ratio(
        image: ImageFile.ImageFile, aspect_ratio: str) -> ImageFile.ImageFile:
    """
    Change image aspect ratio by first trimming transparent areas, then adding white padding.

    Args:
        image: PIL Image object (4 channels RGBA)
        aspect_ratio: String in format "width:height" (e.g., "1:1", "16:9")

    Returns:
        PIL Image with target aspect ratio and white padding
    """
    # Step 1: Trim transparent areas using alpha channel
    alpha = image.split()[-1]  # Get alpha channel
    bbox = alpha.getbbox()  # Find bounding box of opaque pixels
    trimmed_image = image.crop(bbox)  # Crop to remove transparent borders

    current_w, current_h = trimmed_image.size

    # Parse aspect ratio string
    try:
        width_ratio, height_ratio = map(int, aspect_ratio.split(":"))
        target_ratio = width_ratio / height_ratio
    except (ValueError, ZeroDivisionError):
        raise ValueError(
            f"Invalid aspect ratio format: {aspect_ratio}. Expected format: 'width:height'"
        )

    current_ratio = current_w / current_h

    # Calculate target dimensions
    if abs(current_ratio - target_ratio) < 0.001:  # Already correct ratio
        return trimmed_image, False
    elif current_ratio > target_ratio:
        # Image too wide, pad vertically
        new_w = current_w
        new_h = int(current_w / target_ratio)
    else:
        # Image too tall, pad horizontally
        new_h = current_h
        new_w = int(current_h * target_ratio)

    # Create white canvas with same mode as input
    new_image = Image.new(trimmed_image.mode, (new_w, new_h), "white")

    # Calculate center position for pasting
    paste_x = (new_w - current_w) // 2
    paste_y = (new_h - current_h) // 2

    # Paste trimmed image at center
    new_image.alpha_composite(trimmed_image, (paste_x, paste_y))

    return new_image, True

def parse_json_response(response_text: str) -> Dict[str, Any]:
    """Parse JSON response from LLM, extracting JSON from text if needed"""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
    return {
        "asset_similarity_score": -1,
        "asset_visibility": -1,
        "background_user_intent_match": -1,
        "edit_instructions": (
            response_text if response_text else "Continue refinement"
        ),
    }


def process_image_analysis_score(image_analysis: dict) -> dict:
    def safe_round(value):
        """Round value to nearest int if not None, else return 0."""
        if value is None:
            return 0
        try:
            return round(value)
        except (TypeError, ValueError):
            return 0

    scores = image_analysis.get("scores", {})

    color = safe_round(scores.get("color"))
    material = safe_round(scores.get("material"))
    design_style = safe_round(scores.get("design_style"))
    product_type = safe_round(scores.get("product_type"))
    text_similarity = safe_round(scores.get("text_similarity"))
    text_used = scores.get("text_used", False)  # boolean stays as-is

    individual = {
        "color": color,
        "material": material,
        "text_used": text_used,
        "design_style": design_style,
        "product_type": product_type,
        "text_similarity": text_similarity,
    }

    overall = safe_round(image_analysis.get("final_score", 0))

    return {
        "overall": overall,
        "individual": individual,
    }


def send_slack_message(message):

    url = "https://slack.com/api/chat.postMessage"

    if not SLACK_API_KEY:
        print("Slack API Key Not Found")

        return

    channel = f"bugsnag-error-{ENVIRONMENT.lower()}"    
    
    headers = {
        "Authorization": f"Bearer {SLACK_API_KEY}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {"channel": channel, "text": message}
    response = requests.post(url, headers=headers, json=payload)

    data = response.json()

    if data.get('ok'):
        print("Message send successfully")

        return
    
    print(f"Error occured:{data.get('error')}")

def parse_json_from_markdown(md_string: str):
    try:
        if not md_string or not isinstance(md_string, str):
            raise ValueError("Input must be a non-empty string.")

        # 🧹 Step 1: Remove Markdown code fences and leading/trailing spaces
        clean_json = re.sub(r"^```(?:json)?|```$", "", md_string.strip(), flags=re.MULTILINE).strip()

        # 🧩 Step 2: Try parsing JSON directly
        try:
            return json.loads(clean_json)
        except json.JSONDecodeError:
            # 🧠 Step 3: Attempt to fix common formatting issues
            repaired = (
                clean_json
                .replace("'", '"')              # replace single quotes with double quotes
                .replace("\n", "")              # remove line breaks
                .replace(",}", "}")             # remove trailing commas
                .replace(",]", "]")             # remove trailing commas in lists
            )
            return json.loads(repaired)

    except json.JSONDecodeError as e:
        print(f"[JSON Decode Error] {e.msg} at line {e.lineno}, column {e.colno}")
    except ValueError as e:
        print(f"[Value Error] {e}")
    except Exception as e:
        print(f"[Unexpected Error] {e}")

    # Return None if parsing failed
    return None
