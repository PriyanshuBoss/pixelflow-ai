"""
Module for removing backgrounds from images using the FAL.AI rembg API.
"""

import os
import base64
import logging
import mimetypes
import time
import json
import requests
from typing import Dict, Any, Tuple, Optional
from urllib.parse import urlparse

import boto3
import fal_client

from io import BytesIO

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')
sqs_client = boto3.client('sqs')

class BackgroundRemover:
    """
    Class for removing backgrounds from images using the FAL.AI API.
    Provides methods for processing images from S3 or binary data.
    """

    def __init__(self):
        """Initialize the background remover with proper logging and error tracking."""
        self.logger = logger
        self.error_dict = {}

        # Verify FAL_KEY is available
        if not os.environ.get('FAL_KEY'):
            self.logger.error("FAL_KEY environment variable is missing")
            raise ValueError("FAL_KEY environment variable is required")

    def is_s3_path(self, path: str) -> bool:
        """
        Check if the path starts with 's3://' prefix.

        Args:
            path: Path to check

        Returns:
            bool: True if the path is an S3 path, False otherwise
        """
        return path.lower().startswith('s3://')

    def is_local_path(self, path: str) -> bool:
        """
        Check if the path is a local file path that exists on the filesystem.

        Args:
            path: Path to check

        Returns:
            bool: True if the path is a local file path, False otherwise
        """
        return os.path.isfile(path)

    def is_http_url(self, path: str) -> bool:
        """
        Check if the path is an HTTP/HTTPS URL.

        Args:
            path: Path to check

        Returns:
            bool: True if the path is an HTTP/HTTPS URL, False otherwise
        """
        return path.lower().startswith(('http://', 'https://'))

    def download_from_url(self, url: str) -> bytes:
        """
        Download image data from an HTTP/HTTPS URL.

        Args:
            url: HTTP/HTTPS URL to download from

        Returns:
            bytes: Binary image data

        Raises:
            ValueError: If the image cannot be downloaded
        """
        start_time = time.time()
        self.logger.info(f"Downloading image from URL: {url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Check if content type is an image
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                self.logger.warning(f"Content type '{content_type}' may not be an image")

            download_time = time.time() - start_time
            self.logger.info(f"Download completed in {download_time:.2f}s")

            return response.content
        except Exception as e:
            download_time = time.time() - start_time
            self.logger.error(f"Failed to download image from {url} in {download_time:.2f}s: {str(e)}")
            raise ValueError(f"Failed to download image from URL: {str(e)}")

    def read_image(self, path: str) -> bytes:
        """
        Read image data from S3, HTTP URL, or local path.

        Args:
            path: Path to image (s3:// URL, HTTP URL, or local file path)

        Returns:
            bytes: Binary image data

        Raises:
            ValueError: If the image cannot be loaded
        """
        start_time = time.time()
        self.logger.debug(f"Reading image from {path}")

        try:
            if self.is_s3_path(path):
                # Load image from S3
                data = self.load_image_from_s3(path)
            elif self.is_http_url(path):
                # Load image from HTTP URL
                data = self.download_from_url(path)
            elif os.path.isfile(path):
                with open(path, 'rb') as fd:
                    data = fd.read()
            else:
                raise ValueError(f"Unable to load image from {path}: Path is not a valid S3 URL, HTTP URL, or local file")

            read_time = time.time() - start_time
            self.logger.debug(f"Image read completed in {read_time:.2f}s")
            return data

        except Exception as e:
            read_time = time.time() - start_time
            self.logger.error(f"Failed to read image from {path} in {read_time:.2f}s: {str(e)}")
            raise ValueError(f"Failed to read image from {path}: {str(e)}")

    def remove_background_from_binary(self, image_binary: bytes) -> Optional[bytes]:
        """
        Remove background from binary image data without saving to disk.

        Args:
            image_binary: Binary image data

        Returns:
            bytes: Binary data of image with transparent background, or None on failure

        Raises:
            Exception: If background removal fails
        """
        start_time = time.time()
        self.logger.info("Processing binary image data")

        try:
            # Try to detect content type
            content_type = "image/jpeg"  # Default
            try:
                # Try using magic if available
                try:
                    import magic
                    mime = magic.Magic(mime=True)
                    detected_type = mime.from_buffer(image_binary)
                    if detected_type.startswith('image/'):
                        content_type = detected_type
                except ImportError:
                    # If magic is not available, try to detect from header bytes
                    if image_binary.startswith(b'\xff\xd8'):
                        content_type = 'image/jpeg'
                    elif image_binary.startswith(b'\x89PNG\r\n\x1a\n'):
                        content_type = 'image/png'
                    elif image_binary[0:2] == b'BM':
                        content_type = 'image/bmp'
                    elif image_binary.startswith(b'GIF8'):
                        content_type = 'image/gif'
            except Exception as e:
                self.logger.warning(f"Error detecting content type: {str(e)}, using default")

            self.logger.info(f"Processing binary image with content type: {content_type}")

            # Remove background using fal.ai
            job_id = fal_client.upload(image_binary, content_type)
            self.logger.info(f"Uploaded image to FAL.AI, job_id: {job_id}")

            # Add more detailed logging about API call
            self.logger.info("Calling FAL.AI rembg API with parameters: sync_mode=True")

            result = fal_client.subscribe(
                "fal-ai/imageutils/rembg",
                arguments={
                    "image_url": job_id,
                    "sync_mode": True
                }
            )

            # Log the actual result structure (without the full base64 data) for debugging
            result_keys = result.keys() if result else []
            self.logger.info(f"API response keys: {result_keys}")

            if "image" in result:
                image_keys = result["image"].keys() if result["image"] else []
                self.logger.info(f"Image object keys: {image_keys}")

                if "url" not in result["image"]:
                    self.logger.error("Missing 'url' in image object")
            else:
                self.logger.error("Missing 'image' in API response")

            # Check for errors in the API response
            if not result or "image" not in result or "url" not in result["image"]:
                raise ValueError(f"Invalid response from FAL.AI API: {result}")

            # Log information about the returned URL format
            url_preview = result["image"]["url"][:50] + "..." if len(result["image"]["url"]) > 50 else result["image"]["url"]
            self.logger.info(f"Received image URL starting with: {url_preview}")

            # Check if URL is data URL format
            if not result["image"]["url"].startswith("data:"):
                self.logger.error("Unexpected URL format - not a data URL")
                raise ValueError("API did not return a data URL")

            # Extract content type from data URL
            data_url_parts = result["image"]["url"].split(",", 1)
            if len(data_url_parts) != 2:
                raise ValueError("Invalid data URL format")

            header = data_url_parts[0]
            data = data_url_parts[1]

            self.logger.info(f"Data URL header: {header}")

            # Return the processed binary data
            try:
                process_time = time.time() - start_time
                self.logger.info(f"Background removal completed in {process_time:.2f}s")
                return base64.b64decode(data)

            except Exception as decode_error:
                self.logger.error(f"Error decoding image data: {str(decode_error)}")
                raise ValueError(f"Failed to decode image data: {str(decode_error)}")

        except Exception as e:
            process_time = time.time() - start_time
            self.logger.error(f"Error removing background from binary in {process_time:.2f}s: {str(e)}")
            self.error_dict["error"] = str(e)
            self.error_dict["isvalid"] = False
            self.error_dict["processing_time_ms"] = int(process_time * 1000)
            self.error_dict["error_type"] = "api_failure" if "FAL.AI API" in str(e) else "processing_failure"
            return None

    def load_image_from_s3(self, image_path: str) -> bytes:
        """
        Get an image from S3.

        Args:
            image_path: S3 URL (s3://bucket/key)

        Returns:
            bytes: Binary image data

        Raises:
            Exception: If the image cannot be fetched from S3
        """
        # Parse the S3 URL
        bucket_name, key = image_path.replace("s3://", "").split("/", 1)

        try:
            # Get the image from S3
            self.logger.debug(f"Fetching object from S3: bucket={bucket_name}, key={key}")
            response = s3_resource.Object(bucket_name, key).get()
            return response['Body'].read()
        except Exception as e:
            self.logger.error(f"Error loading image from S3: {str(e)}")
            raise ValueError(f"Failed to load image from S3: {str(e)}")

    def add_suffix_to_filename(self, image_path: str, suffix: str="bg_removed") -> str:
        """
        Add a suffix to a filename before the extension.

        Args:
            image_path: Path to image
            suffix: Suffix to add (default: "bg_removed")

        Returns:
            str: New filename with suffix
        """
        # Extract the filename and extension from the path
        file_name, file_extension = os.path.splitext(image_path)

        # Add the suffix before the file extension
        new_file_name = f"{file_name}_{suffix}.png"

        return new_file_name

    def upload_image_to_s3(self, bucket_name: str, object_key: str, image_data: bytes) -> None:
        """
        Upload an image to S3.

        Args:
            bucket_name: S3 bucket name
            object_key: S3 object key
            image_data: Binary image data

        Raises:
            Exception: If the upload fails
        """
        try:
            # Upload the image to S3
            self.logger.info(f"Uploading processed image to S3: bucket={bucket_name}, key={object_key}")
            s3_resource.Object(bucket_name, object_key).put(
                Body=image_data,
                ContentType='image/png'
            )
            self.logger.info(f"Upload complete: s3://{bucket_name}/{object_key}")
        except Exception as e:
            self.logger.error(f"Error uploading to S3: {str(e)}")
            raise ValueError(f"Failed to upload image to S3: {str(e)}")

    def send_callback_message(self, queue_url: str, message_data: Dict[str, Any]) -> None:
        """
        Send a callback message to the specified SQS queue.

        Args:
            queue_url: SQS queue URL
            message_data: Message data to send

        Raises:
            Exception: If sending the message fails
        """
        try:
            self.logger.info(f"Sending callback to SQS queue: {queue_url}")
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_data)
            )
            self.logger.info("Callback sent successfully")
        except Exception as e:
            self.logger.error(f"Error sending callback message: {str(e)}")
            # Don't raise here - we don't want to fail the whole process if just the callback fails

    def remove_background(self, image_path: str, output_key_prefix: str = None,
                          callback_queue_url: str = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Remove background from an image at the specified path.

        Args:
            image_path: Path to image (s3:// URL or local file path)
            output_key_prefix: Prefix for output object key (optional)
            callback_queue_url: SQS queue URL for callback (optional)

        Returns:
            Tuple of (output_path, error_dict)
        """
        metrics = {}
        start_time = time.time()
        self.error_dict = {}  # Reset error dict

        try:
            # Get content type if possible
            mt = mimetypes.guess_type(image_path)
            content_type = None
            if mt and len(mt) > 0:
                content_type = mt[0]

            # Read the image
            data = self.read_image(image_path)
            if data is None:
                raise ValueError(f"Failed to read image at {image_path}")

            self.logger.info(f"Successfully read {len(data)} bytes from {image_path}")

            # Remove background using fal.ai
            self.logger.info(f"Processing image at {image_path}")
            processed_data = self.remove_background_from_binary(data)

            if not processed_data:
                raise ValueError("Background removal failed, no processed data returned")

            self.logger.info(f"Successfully processed image, received {len(processed_data)} bytes")

            # Save the output image
            if self.is_s3_path(image_path):
                # S3 path handling
                bucket_name, filename = image_path.replace("s3://", "").split("/", 1)

                # Use the provided output key prefix if available
                if output_key_prefix:
                    base_filename = os.path.basename(filename)
                    output_path = f"{output_key_prefix.rstrip('/')}/{base_filename.split('.')[0]}_mask.png"
                else:
                    output_path = self.add_suffix_to_filename(filename)

                # Upload to S3
                self.upload_image_to_s3(bucket_name, output_path, processed_data)

                # Construct full S3 URL for the output path
                full_output_path = f"s3://{bucket_name}/{output_path}"
                self.logger.info(f"Saving result to {full_output_path}")
            else:
                # Local file handling
                output_path = self.add_suffix_to_filename(image_path)
                with open(output_path, "wb") as f:
                    f.write(processed_data)
                full_output_path = output_path
                self.logger.info(f"Saving result to {full_output_path}")

            # Calculate total time
            end_time = time.time()
            process_time_ms = int((end_time - start_time) * 1000)
            metrics['total_bg_removal_time_ms'] = process_time_ms
            self.logger.info(f"Background removal completed in {process_time_ms}ms")

            # Send callback if requested
            if callback_queue_url:
                callback_message = {
                    "original_image_key": image_path,
                    "mask_image_key": full_output_path,
                    "success": True,
                    "processing_time_ms": process_time_ms
                }
                self.send_callback_message(callback_queue_url, callback_message)

            return full_output_path, self.error_dict

        except Exception as e:
            # Handle errors
            end_time = time.time()
            process_time_ms = int((end_time - start_time) * 1000)

            self.logger.error(f"Error removing background from {image_path}: {str(e)}")

            self.error_dict["error"] = str(e)
            self.error_dict["isvalid"] = False
            self.error_dict["processing_time_ms"] = process_time_ms
            self.error_dict["error_type"] = "api_failure" if "FAL.AI API" in str(e) else "processing_failure"

            # Send error callback if requested
            if callback_queue_url:
                error_message = {
                    "original_image_key": image_path,
                    "success": False,
                    "error_type": self.error_dict["error_type"],
                    "error_message": str(e)
                }
                self.send_callback_message(callback_queue_url, error_message)

            return None, self.error_dict
