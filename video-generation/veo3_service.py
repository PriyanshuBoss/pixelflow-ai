import base64
import copy
import time
from io import BytesIO

from google import genai
from google.genai import (
    types,
)  # Ensure this import is correct based on your SDK version
from PIL import Image

from common.utils import send_slack_message
from constants import PROJECT_ID, LOCATION_ID


def pil_image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """Convert PIL Image to bytes."""
    buffer = BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


def pil_image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Convert PIL Image to base64 string."""
    buffer = BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_video(request_json):
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION_ID,
    )
    model_name = "veo-3.1-generate-preview"
    aspect_ratio = request_json["aspect_ratio"]

    # Convert PIL image to bytes
    first_frame_image_bytes = request_json["first_frame"].image_bytes

    # Create Image object with image_bytes and mime_type
    first_frame_image = types.Image(
        image_bytes=first_frame_image_bytes, mime_type="image/png"
    )

    try:
        # Check if the video is the last segment
        if request_json.get("last_frame") == "final_segment":
            print(
                "[VEO_3_SERVICE]: This is the last segment, running with single image video generation."
            )
            operation = client.models.generate_videos(
                model=model_name,
                prompt=request_json["prompt"],
                image=first_frame_image,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    number_of_videos=1,
                    generate_audio=False,
                    person_generation=types.PersonGeneration.ALLOW_ALL,
                    duration_seconds=8,
                ),
            )
        else:
            print(
                "[VEO_3_SERVICE]: This is not the last segment, running with last frame video generation."
            )
            # Adding last frame to the request
            last_frame_image_bytes = request_json["last_frame"].image_bytes
            last_frame_image = types.Image(
                image_bytes=last_frame_image_bytes, mime_type="image/png"
            )
            operation = client.models.generate_videos(
                model=model_name,
                prompt=request_json["prompt"],
                image=first_frame_image,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    number_of_videos=1,
                    generate_audio=False,
                    person_generation=types.PersonGeneration.ALLOW_ALL,
                    duration_seconds=8,
                    last_frame=last_frame_image,
                ),
            )
            print("Triggered last frame generation successfully")

    except Exception as e:
        print(
            f"[VEO_3_SERVICE]: Error occurred: {e}\nUsing default default single image video generation flow."
        )

        if hasattr(e, "code") and e.code == 429:
            print("Quota exceeded. Retrying in 60 seconds...")
            time.sleep(60)

        operation = client.models.generate_videos(
            model=model_name,
            prompt=request_json["prompt"],
            image=first_frame_image,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=1,
                duration_seconds=request_json["segment_duration"],
            ),
        )

    operation_id = getattr(operation, "name", None)

    if not operation_id:
        return {
            "operation_id": "",
            "error_message": "operation_id not found",
            "status": "error",
            "segment_number": request_json.get("segment_number", 1),
            "duration": request_json.get("duration", 8),
            "vendor": "veo3",
            "video_url": "",
            "created_at": time.time(),
            "prompt": request_json.get(
                "prompt",
                "A cinematic tracking shot through a magical ice cave, massive crystalline icicles hanging from the ceiling, glowing with an ethereal blue light. The camera gracefully moves between the translucent formations, capturing the slow drips of water that create rainbow-like refractions. The scene has a dreamy, otherworldly quality with misty air and subtle particles floating in the beams of light",
            ),
            "model": model_name,
            "progress": 0,
        }

    print(f"{operation = }")

    while not operation.done:
        time.sleep(10)
        operation = client.operations.get(operation)

    print(f"{operation.response = }")

    random_suffix = int(time.time())
    fname = f"{request_json['segment_index']}_{random_suffix}.mp4"

    if not operation.response or not getattr(
        operation.response, "generated_videos", None
    ):

        request_json_copy = copy.deepcopy(request_json)
        request_json_copy.pop("gemini_api_key", None)

        error_message = f"No video generated for {request_json_copy}. The Response coming from service is {operation.response}"
        print(error_message)

        send_slack_message(error_message)

        return {}

    vid = operation.response.generated_videos[0]

    return {"file_bytes": vid.video.video_bytes, "fname": fname}
