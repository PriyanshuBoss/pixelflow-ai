import base64
import io
import os

import requests

from PIL import Image, ImageFile


class AssetProcessor:

    @staticmethod
    def convert_asset_url_to_base64(asset_url: str) -> str:
        try:
            if asset_url.startswith("http://") or asset_url.startswith("https://"):

                response = requests.get(asset_url)
                response.raise_for_status()
                data = response.content
            else:

                if not os.path.exists(asset_url):
                    raise FileNotFoundError(f"File not found: {asset_url}")
                with open(asset_url, "rb") as f:
                    data = f.read()

            # Encode to base64
            return base64.b64encode(data).decode("utf-8")

        except Exception as e:
            raise ValueError(f"Failed to convert asset to base64: {e}")


    @staticmethod
    def extract_bg_removed_asset(asset_url):
       base, ext = os.path.splitext(asset_url)
       supported = {".png", ".jpg", ".jpeg", ".webp"}

       if ext.lower() in supported:
            return f"{base}_bg_removed.png"

       return asset_url

    @staticmethod
    def get_image_from_bytes(image_stream: bytes) -> ImageFile.ImageFile:
        return Image.open(io.BytesIO(image_stream.image_bytes))


    @staticmethod
    def get_image_from_base64(b64_image: str) -> ImageFile.ImageFile:
        if b64_image:
            image_bytes = base64.b64decode(b64_image)
            image_stream = io.BytesIO(image_bytes)
            img = Image.open(image_stream)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            return img
        return None
