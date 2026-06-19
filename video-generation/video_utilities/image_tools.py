import os
import subprocess
import tempfile

from PIL import Image


class ImageTools:

    @staticmethod
    def check_and_change_image_aspect_ratio(image, aspect_ratio: str):
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
            return trimmed_image
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

        print(f"New image size: {new_image.size}")
        return new_image

    @staticmethod
    def merge_videos(video_path_list, output_path):
        """
        Merge multiple videos into a single video file using ffmpeg.

        Args:
            video_path_list: List of video file paths to merge (in order)
            output_path: Path for the output merged video file

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ValueError: If video_path_list is empty or contains invalid paths
            RuntimeError: If ffmpeg command fails
        """
        if not video_path_list:
            raise ValueError("video_path_list cannot be empty")

        # Validate all video paths exist
        for video_path in video_path_list:
            if not os.path.exists(video_path):
                raise ValueError(f"Video file not found: {video_path}")

        # Create temporary file list for ffmpeg concat demuxer
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            file_list_path = f.name
            for video_path in video_path_list:
                # Use absolute paths and escape for ffmpeg
                abs_path = os.path.abspath(video_path)
                f.write(f"file '{abs_path}'\n")

        try:
            # Use ffmpeg concat demuxer to merge videos
            cmd = [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                file_list_path,
                "-c",
                "copy",  # Copy codec without re-encoding for speed
                "-y",  # Overwrite output file if exists
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            print(
                f"Successfully merged {len(video_path_list)} videos into {output_path}"
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error merging videos: {e.stderr}")
            raise RuntimeError(f"ffmpeg command failed: {e.stderr}")

        finally:
            # Clean up temporary file
            if os.path.exists(file_list_path):
                os.remove(file_list_path)

