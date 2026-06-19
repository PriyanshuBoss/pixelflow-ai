import os

# Script and keyframe generator prompts
SCRIPT_GENERATOR_PROMPT_KEY = "script_generator_2"
SCRIPT_ANALYZER_PROMPT_KEY = "script_analyzer_2"


INPUT_IMAGE_PATH = "mayo_yellow.png"
OUTPUT_PATH = "output"
ASPECT_RATIO = "9:16"


VIDEO_DURATION = 25
PROMPT = "Create a scene with the mayo bottle being used in a professional kitchen by a masterful chef. Add B roll of salad dressing. Keep the scene photorealistic."


REQUEST_CONFIG = {
    "gemini_image_api_key": os.getenv("GEMINI_API_KEY", ""),
    "gemini_video_api_key": os.getenv("GEMINI_VIDEO_API_KEY", ""),
    "script_generator_prompt_key": SCRIPT_GENERATOR_PROMPT_KEY,
    "script_analyzer_prompt_key": SCRIPT_ANALYZER_PROMPT_KEY,
    "aspect_ratio": ASPECT_RATIO,
    "input_image_path": INPUT_IMAGE_PATH,
    "output_dir_path": OUTPUT_PATH,
    "video_duration": VIDEO_DURATION,
    "prompt": PROMPT,
}

