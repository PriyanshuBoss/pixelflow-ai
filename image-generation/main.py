#!/usr/bin/env python
import io
import json
import os
import re
import time
import traceback
import uuid
from typing import Any, Dict, List, Optional

import boto3
import requests
from constants import SUPPORTED_ASPECT_RATIO
from PIL import Image, ImageFile
from prompt_templates import (
    AgentConfig,
    generate_brand_voice_section,
    generate_human_check_prompt,
    generate_human_parameters_section,
)
from watermark import watermark_from_url

from common.asset_processor import AssetProcessor
from common.flux_client import FluxClient
from common.image_analyser import ImageAnalyser
from common.nano_banana_client import NanaBananaChat
from common.custom_openai_client import CustomOpenAIClient
from common.utils import (
    check_and_change_image_aspect_ratio,
    process_image_analysis_score,
    setup_logger,
)


class Consumer:

    _variant_agent_map = {
        "fashion": "fashion_generator",
        "default": "background_generator",
    }

    _variant_editing_expert_map = {
        "fashion": "fashion_editing_expert",
        "default": "image_editing_expert",
    }

    _variant_title_caption_generator_map = {
        "fashion": "image_title_caption_generator",
        "default": "image_title_caption_generator",
    }
    __name__ = "ideas-nano"

    def __init__(self, api_key: str, message: Optional[dict] = None):
        self.asset_base64 = ""
        self.s3_client = boto3.client("s3")
        self.bucket = os.getenv("BUCKET", "staging-gaana")
        self.message = message or {}
        self.request_data = {}
        self.sqs = boto3.client("sqs")
        self.output_queue_url = self.get_sqs_queue(
            os.getenv("PROMPT_OUTPUT_QUEUE_URL", "push-generated-content-db-staging")
        )
        self.context = {"logs": []}
        self.image_analysis = {}
        self.client = NanaBananaChat(api_key)
        self.flux_client = FluxClient()
        self.agent_config = AgentConfig()
        self.iterations = int(os.getenv("ITERATION", "1"))
        self.logger = setup_logger(__name__)
        self.generated_images = []
        self.aspect_ratio = "1:1"
        self.node = "current-v1"
        self.is_edit = False
        self.asset_records = []

        self.visual_index = None
        self.aspect_ratio = ""

    def get_sqs_queue(self, queue_name):
        try:
            if queue_name.startswith("https://"):

                return queue_name
            sqs = boto3.resource("sqs")
            queue = sqs.get_queue_by_name(QueueName=queue_name)

            return queue.url  # Return the URL string instead of Queue object
        except Exception as e:
            self.logger.error("Error fetching Queue", e)

    def send_to_output_queue(self, message) -> bool:
        try:
            self.logger.info(f"Output Queue URL: {self.output_queue_url}")
            self.logger.info(
                f"Message to be pushed to queue: {json.dumps(message, indent=2)}"
            )
            response = self.sqs.send_message(
                QueueUrl=self.output_queue_url, MessageBody=json.dumps(message)
            )
            self.logger.info(
                f"Message sent to output queue. MessageId: {response.get('MessageId')}"
            )

            return True
        except Exception as e:
            self.logger.info(f"{traceback.print_exc()}")
            self.logger.info(f"Error sending message to output queue: {str(e)}")

            return False

    def set_log(self, data: dict):
        if "logs" not in self.context:
            self.context["logs"] = []
        self.context["logs"].append(data)

    def upload_file_object(
        self, image_stream: bytes, object_name: str, content_type: str
    ) -> str:
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=object_name,
            Body=image_stream,
            ContentType=content_type,
            CacheControl="public, max-age=0, must-revalidate",
        )

        return f"https://{self.bucket}.s3.amazonaws.com/{object_name}"

    def upload_file_from_url(self, image_url, name, ext, suffix="_upscaled"):
        """
        Downloads an image from a URL and uploads it to S3 with a modified path:
        original filename + '_upscaled' + original extension
        """
        # Download the image
        response = requests.get(image_url)

        if response.status_code != 200:
            raise ValueError(f"Failed to download image from URL: {image_url}")

        image_stream = response.content
        content_type = response.headers.get("Content-Type", "application/octet-stream")

        # Create new S3 object name with '_upscaled' suffix
        object_name = f"{name}{suffix}{ext}"

        # Upload to S3
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=object_name,
            Body=image_stream,
            ContentType=content_type,
        )

        return f"https://{self.bucket}.s3.amazonaws.com/{object_name}"

    def set_request_data_for_compute(self):
        generated_config_id = self.message.get("id")
        brand_id = self.message.get("brand_id")

        items = self.message.get("items", [{}])[0]

        asset_url_list = items.get("assets", []) or [""]
        variants_list = items.get("variants", []) or ["default"]
        descriptions_list = items.get("descriptions", [])

        post_type = items.get("post_type", "image")

        if post_type == "image":

            # If post type is image and asset len is > 1 then we will use the multi-sku flow. Fashion is excluded
            if len(asset_url_list) > 1:
                self.node = "current-v1-multi-products"
            #     asset_url_list = asset_url_list[:1]

            if len(variants_list) > 1:
                variants_list = variants_list[:1]

            if len(descriptions_list) > 1:
                descriptions_list = descriptions_list[:1]

        if not descriptions_list:
            descriptions_list = [{}] * len(asset_url_list)

        # this will make sure that below for loop on asset_url_list avoid index error while accessing variants_list
        if len(variants_list) != len(asset_url_list):
            variants_list = variants_list[:1] * len(asset_url_list)

        # this will make sure that below for loop on asset_url_list avoid index error while accessing descriptions_list
        if len(descriptions_list) != len(asset_url_list):
            descriptions_list = descriptions_list[:1] * len(asset_url_list)

        if not self.aspect_ratio:
            self.aspect_ratio = (
                self.message.get("items", [{}])[0]
                .get("metadata", {})
                .get("aspect_ratio", "1:1")
            )

        description = self.message.get("content_pillar", {}).get("description")

        self.brand_name = self.message.get("brand_name", "current").lower()

        self.is_edit = self.message.get("visual_tweak")

        if self.is_edit:
            description = self.message.get("tweak") or description

        visual_index = self.message.get("visual_index")

        if visual_index is not None:
            self.visual_index = int(visual_index)
            asset_url = self.message["generated_content"][visual_index]["link"]

            self.asset_records.append(
                {
                    "url": asset_url,
                    "path": f"assets/{brand_id}/generated_config/{generated_config_id}/ideas-nano/{uuid.uuid4()}",
                    "asset_base64": AssetProcessor.convert_asset_url_to_base64(
                        asset_url
                    ),
                    "variant": variants_list[visual_index],
                    "description": descriptions_list[visual_index].get(
                        "description", ""
                    ),
                }
            )

        else:

            for i in range(len(asset_url_list)):
                bg_removed = AssetProcessor.extract_bg_removed_asset(asset_url_list[i])

                self.asset_records.append(
                    {
                        "url": bg_removed,
                        "path": f"assets/{brand_id}/generated_config/{generated_config_id}/ideas-nano/{uuid.uuid4()}",
                        "asset_base64": (
                            AssetProcessor.convert_asset_url_to_base64(bg_removed)
                            if bg_removed
                            else ""
                        ),
                        "variant": variants_list[i],
                        "description": descriptions_list[i].get("description", ""),
                    }
                )

        temp = {
            "description": description,
            "brand_name": self.brand_name,
            "asset_records": self.asset_records,
        }

        self.request_data.update(temp)

    def analyse_similarity_between_images(self, asset_base64: List[str], s3_url: str):
        # if no assets passed then we don't have anything to score
        if not asset_base64:
            return {}
        output_image_base64 = AssetProcessor.convert_asset_url_to_base64(s3_url)
        asset_base64_list = []
        asset_base64_list.append(asset_base64)
        asset_base64_list.append(output_image_base64)

        image_analyser = ImageAnalyser(asset_base64_list)

        return image_analyser.analyse_image_similarity()

    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, extracting JSON from text if needed"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    return {}

    def generate_title_caption(self, user_prompt: str, variant: str):
        context_prompt = f"User Request: {user_prompt}"
        agent_name = (
            self._variant_title_caption_generator_map.get(variant)
            or self._variant_title_caption_generator_map["default"]
        )
        prompt_config = self.agent_config.get(agent_name)
        title_caption_system_prompt = prompt_config.get(self.node) or prompt_config.get(
            "current"
        )
        title_caption_full_prompt = f"{title_caption_system_prompt}\n\n{context_prompt}"
        title_caption = self.parse_json_response(
            self.client.call_llm(agent_name, [title_caption_full_prompt])
        )
        self.set_log(
            {
                "input": title_caption_full_prompt,
                "output": title_caption,
                "model": self.client._llm_model,
            }
        )
        self.logger.info(f"Title Caption: {title_caption}")

        return {
            "post_caption": title_caption.get("post_caption", ""),
            "post_title": title_caption.get("post_title", ""),
        }

    def get_watermark_on_image(self, s3_url):
        """
        Download image from S3 URL, apply watermark, and upload back to S3.
        Returns the S3 URL of the watermarked image or empty string on failure.
        """
        try:
            print(f"[INFO] Starting watermark process for image URL: {s3_url}")

            # Generate target object name
            object_name = f"assets/{self.message.get('brand_id')}/generated_config/ideas-nano/{uuid.uuid4()}.png"
            print(f"[INFO] Generated S3 object name: {object_name}")

            # Apply watermark
            print("[INFO] Applying watermark...")
            watermarked_image = watermark_from_url(s3_url)

            if not watermarked_image:
                print(f"[ERROR] Watermarking failed for {s3_url}")
                return ""

            print(
                f"[INFO] Watermark applied successfully. Image size: {watermarked_image.size}, Mode: {watermarked_image.mode}"
            )

            # Save image to bytes buffer
            buffer = io.BytesIO()
            watermarked_image.save(buffer, format="PNG")
            buffer.seek(0)
            image_bytes = buffer.getvalue()
            print(
                f"[INFO] Watermarked image saved to bytes. Size: {len(image_bytes)} bytes"
            )

            # Upload to S3
            print(f"[INFO] Uploading watermarked image to S3 at {object_name}...")
            watermark_s3_url = self.upload_file_object(
                image_stream=image_bytes,
                object_name=object_name,
                content_type="image/png",
            )

            print(
                f"[INFO] Upload successful. Watermarked image S3 URL: {watermark_s3_url}"
            )

            return watermark_s3_url

        except Exception as e:
            print(f"[ERROR] Exception in get_watermark_on_image: {e}")
            return ""

    def process_s3_url_list(self, s3_url_list):

        caption = ""
        scores_list = []
        metadata = {"logs": self.context["logs"]}

        if self.visual_index is not None and s3_url_list:
            generated_content = self.message.get("generated_content", [])
            generated_content_data = generated_content[self.visual_index]
            data = s3_url_list[0]
            post_title = generated_content_data.get("post_title")
            post_caption = generated_content_data.get("caption")
            scores = process_image_analysis_score(data.get("image_analysis"))

            caption = self.message.get("caption")
            watermark_s3_url = self.get_watermark_on_image(data.get("s3_url"))

            entry = {
                "link": data.get("s3_url"),
                "watermark_s3_url": watermark_s3_url,
                "caption": post_caption,
                "post_title": post_title,
                "resolution": data.get("image_dimensions"),
                "scores": scores,
                "aspect_ratio": self.aspect_ratio,
            }

            generated_content[self.visual_index] = entry

        else:
            generated_content = []

            for data in s3_url_list:

                if not caption:
                    caption = data.get("post_caption")

                post_title = data.get("post_title")
                post_caption = data.get("post_caption")
                scores = process_image_analysis_score(data.get("image_analysis"))
                scores_list.append(scores)

                watermark_s3_url = self.get_watermark_on_image(data.get("s3_url"))

                entry = {
                    "link": data.get("s3_url"),
                    "watermark_s3_url": watermark_s3_url,
                    "caption": post_caption,
                    "post_title": post_title,
                    "resolution": data.get("image_dimensions"),
                    "scores": scores,
                    "aspect_ratio": self.aspect_ratio,
                }

                generated_content.append(entry)

        metadata["image_analysis"] = [item["scores"] for item in generated_content]

        return generated_content, caption, metadata

    def set_response_data_for_backend(self, s3_url_list):

        response = {
            "generate_config": self.message.get("id"),
            "idea": "",
            "generated_content_description": [],
            "scheduled_at": 0,
            "brand_id": self.message.get("brand_id"),
            "status": "success",
            "caption": "",
            "generated_content_links": [],
            "visual_tweak": self.is_edit,
            "visual_index": self.visual_index,
        }

        generated_content, caption, metadata = self.process_s3_url_list(s3_url_list)

        response["generated_content"] = generated_content
        response["caption"] = caption
        response["metadata"] = metadata

        if self.message.get("generated_post_id"):
            response["generated_post_id"] = self.message["generated_post_id"]

        return response


    def validate_image_require_human_or_not(self, system_description, user_description):

        prompt = generate_human_check_prompt(system_description, user_description)
        client = CustomOpenAIClient()
        response = client.call_open_ai({"prompt_text": prompt})

        return response == "Yes"


    def get_detailed_prompt(
        self, context_prompt: str, images: ImageFile.ImageFile, variant: str, record
    ):
        agent_name = (
            self._variant_agent_map.get(variant) or self._variant_agent_map["default"]
        )
        prompt_config = self.agent_config.get(agent_name)

        content_kit = self.message.get("content_kit", {})
        human_kit = self.message.get("human_kit")
        print(f"human_kit: {human_kit}")

        if not human_kit:
            human_kit = {}

        region = content_kit.get("region")



        is_human_required = self.validate_image_require_human_or_not(self.request_data.get('description'), record.get('description', ""))

        print(f"{is_human_required = }")

        if is_human_required:
            user_params = human_kit.get("user_params", {})
            user_params["region"] = region
            user_params = generate_human_parameters_section(user_params)

        else:
            user_params = ""

        brand_voice = generate_brand_voice_section(content_kit.get("brand_voice", {}))

        system_prompt = prompt_config.get(self.node).format(
            user_params=user_params, brand_voice=brand_voice
        )
        full_prompt = f"{system_prompt}\n\n{context_prompt}"

        if images:
            prompt_parts = [full_prompt] + images
        else:
            prompt_parts = [full_prompt]

        prompt = self.client.call_llm(agent_name, prompt_parts)
        self.set_log(
            {
                "input": full_prompt,
                "output": prompt,
                "model": self.client._llm_model,
            }
        )

        return prompt

    def generate_image(
        self, pil_images: List[ImageFile.ImageFile], user_prompt, record
    ):
        images = []

        # if it's visual tweak then image will not have alpha channel and then check and change function
        # throw error `image has wrong mode` as generated_image does not have alpha layer
        if self.is_edit:
            images, modified = pil_images, False
        else:
            for image in pil_images:
                image, modified = check_and_change_image_aspect_ratio(
                    image, self.aspect_ratio
                )
                images.append(image)

        prompt_config = self.agent_config.get("set_base")
        base_instruction = prompt_config.get(self.node) or prompt_config.get("current")
        self.client.set_base(images, base_instruction)

        variant = record.get("variant")
        image_description = record.get("description")
        asset_path = record.get("path")

        self.set_log(
            {
                "aspect_ratio_modified": modified,
                "input": f"setting base image for {variant = }",
                "output": "Base image set successfully",
                "model": self.client._chat_model,
            }
        )

        if not image_description:
            context_prompt = f"User Request: {user_prompt}"
        else:
            context_prompt = (
                f"Idea: {user_prompt}\nImage requirements: {image_description}"
            )

        self.logger.info(f"{context_prompt=}")
        ref_images = []

        if not self.is_edit:
            detailed_prompt = self.get_detailed_prompt(context_prompt, images, variant, record)
            human_kit = self.message.get("human_kit", {})

            if not human_kit:
                human_kit = {}

            media_urls = human_kit.get("media_urls")
            media_url = media_urls[0] if media_urls else None

            print(f"{media_url=}")

            if media_url:
                media_url = AssetProcessor.extract_bg_removed_asset(media_url)
                response = requests.get(media_url)
                response.raise_for_status()
                image_pil = Image.open(io.BytesIO(response.content))
                ref_images.append(image_pil)

                print(f"{ref_images = }")

        else:
            detailed_prompt = user_prompt

        self.logger.info(f"{detailed_prompt=}")

        generated_image = self.client.edit_image(
            detailed_prompt, self.aspect_ratio, request_payload={"images": ref_images}
        )

        final_width, final_height = Image.open(
            io.BytesIO(generated_image.image_bytes)
        ).size
        self.logger.info(f"Image dimensions: {final_width}, {final_height}")
        path = f"{asset_path}.png"
        s3_url = self.upload_file_object(
            generated_image.image_bytes, path, generated_image.mime_type
        )

        self.logger.info(f"inital background add {s3_url = }")
        self.generated_images.append(s3_url)
        self.set_log(
            {
                "input": detailed_prompt,
                "output": s3_url,
                "model": self.client._chat_model,
            }
        )

        return s3_url, [final_width, final_height]

    def create_transparent_image_for_non_sku(self, aspect_ratio: str) -> Image.Image:
        """
        Create and return a transparent PIL Image object for a given aspect ratio.
        """

        if aspect_ratio not in SUPPORTED_ASPECT_RATIO:
            raise ValueError(
                f"Unsupported aspect ratio: '{aspect_ratio}'. "
                f"Choose from {list(SUPPORTED_ASPECT_RATIO.keys())}"
            )

        width, height = SUPPORTED_ASPECT_RATIO[aspect_ratio]

        # Create a transparent image (RGBA mode supports alpha channel)
        im = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        width, height = im.size

        return im

    def compute(self):

        user_prompt = self.request_data["description"]
        s3_url_list = []
        images = []

        for record in self.asset_records:

            if record.get("asset_base64"):
                images.append(
                    AssetProcessor.get_image_from_base64(record.get("asset_base64"))
                )

        if len(images) == 0:
            images = [self.create_transparent_image_for_non_sku(self.aspect_ratio)]

        s3_url, image_dimensions = self.generate_image(images, user_prompt, record)

        print(f"{image_dimensions = }")

        temp = {
            "s3_url": s3_url,
            "image_dimensions": image_dimensions,
        }

        if not self.is_edit:
            post_title_details = self.generate_title_caption(
                user_prompt, self.asset_records[0].get("variant")
            )
            temp.update(post_title_details)

        # need to think on asset similarity score for mutli image usecase for now we are handling
        # single image use case only for multi image score might come low
        image_analysis = self.analyse_similarity_between_images(
            self.asset_records[0].get("asset_base64"), s3_url
        )
        temp["image_analysis"] = image_analysis

        s3_url_list.append(temp)

        self.logger.info(f"{s3_url_list}=")

        return s3_url_list

    def process_message(self, message: dict) -> dict:
        start_time = int(time.time())

        self.logger.info(f"Starting Time of {self.__name__} Processing : {start_time}")
        self.message = message
        brand_name = message.get("brand_name") or ""

        if "watch" in brand_name.lower():
            self.node = "experimental"

        try:
            self.set_request_data_for_compute()
            s3_url_list = self.compute()
            response = self.set_response_data_for_backend(s3_url_list)
            end_time = int(time.time())
            diff = end_time - start_time
            self.logger.info(f"Processing Time for {self.__name__} : {diff}")

            return {"success": True, "output_format": response}
        except Exception as e:
            self.logger.error(f"{traceback.print_exc()}")
            self.logger.info(f"Error Occurend:{e}")
            self.logger.info(f"{self.context = }")

            return {"success": False, "error_message": str(e)}


if __name__ == "__main__":

       with open("data.json", "r", encoding="utf-8") as f:
           data = json.load(f)

       consumer = Consumer(api_key=os.getenv("GEMINI_API_KEY"))
       consumer.logger.info(consumer.process_message(data))
