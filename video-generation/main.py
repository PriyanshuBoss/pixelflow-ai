import io
import json
import os
import time

import boto3
from common.utils import parse_json_from_markdown, send_slack_message
from constants import THUMBNAIL_URL, VIDEO_BASE_PATH
from image_generator import ImageGenerator
from nano_banana_chat import NanoBananaChat
from PIL import Image
from prompt_templates import (
    AgentConfig,
    build_regeneration_prompt,
    create_prompt_for_post_and_caption,
    create_prompt_for_summary_generation,
    generate_brand_voice_section,
    generate_human_check_prompt,
    generate_human_parameters_section,
    generate_product_scene_validation_prompt,
    generate_prompt_for_product_description,
    update_keyframe_prompt_for_end_video_generation,
    update_keyframe_prompt_for_first_video_generation,
    update_keyframe_prompt_for_middle_video_generation,

)
from veo3_service import generate_video
from video_utilities.utils import UtilityTools
from video_utilities.validations import ValidationTools
from video_utilities.video_merger import  merge_videos_with_mediaconvert

from common.asset_processor import AssetProcessor
from common.custom_openai_client import CustomOpenAIClient


class VideoGenerator:
    def __init__(self):

        self.gemini_image_api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_video_api_key = os.getenv("GEMINI_VIDEO_API_KEY", "")

        self.s3_client = boto3.client("s3")
        self.bucket = os.getenv("BUCKET", "staging-gaana")
        self.sqs = boto3.client("sqs")

        self.output_queue_url = self.get_sqs_queue(
            os.getenv("PROMPT_OUTPUT_QUEUE_URL", "push-generated-content-db-staging")
        )

        self.video_config = {}
        self.image_generator = {}

        self.chat_script = NanoBananaChat(self.gemini_image_api_key)
        self.chat_image = NanoBananaChat(self.gemini_image_api_key)

        self.agent_config = AgentConfig()
        self.agent_prompt_config = self.agent_config.get("prompt_library")

        self.script_generator_system_prompt = self.agent_prompt_config.get(
            "script_generator_6", ""
        )
        self.script_analyzer_system_prompt = self.agent_prompt_config.get(
            "script_analyzer_6", ""
        )

        self.script_analyzer_output_format = "JSON output format:\n" + str(
            [
                {
                    "keyframe_number": 0,
                    "keyframe_type": "product_shot or b_roll",
                    "keyframe_prompt": "",
                    "video_segment_duration": "int 8",
                    "segment_video_prompt": "",
                }
            ]
        )

        self.script = ""
        self.post_title = ""
        self.product_description = ""

        self.request_data = {}
        self.keyframe_metadata = []
        self.resolution = [768, 1344]
        self.thumbnail = THUMBNAIL_URL

        self.summary = ""
        self.video_inputs = {}

    def send_to_output_queue(self, message) -> bool:

        print("=== [send_to_output_queue] Starting ===")
        print(f"[DEBUG] Queue URL: {self.output_queue_url}")

        try:

            response = self.sqs.send_message(
                QueueUrl=self.output_queue_url, MessageBody=json.dumps(message)
            )
            print(f"[INFO] Message sent successfully. SQS response: {response}")

            return True
        except Exception as e:
            print(f"[ERROR] Failed to send message to SQS: {e}")

            return False

    def get_sqs_queue(self, queue_name):
        try:
            if queue_name.startswith("https://"):

                return queue_name
            sqs = boto3.resource("sqs")
            queue = sqs.get_queue_by_name(QueueName=queue_name)

            return queue.url  # Return the URL string instead of Queue object
        except Exception as e:
            self.logger.error("Error fetching Queue", e)

    def generate_segments_from_script(self, full_prompt, image, chat):
        try:
            response = chat.send_message_with_images(
                full_prompt, image, self.video_config.get("aspect_ratio", "")
            )

            #print(f"response from segment generation= {response}")

            script = UtilityTools.exract_text_from_chat_response(response)

            if not script or not script.strip():
                raise ValueError("Invalid response from generate_script")

            return script.strip()

        except Exception as e:
            print(f"Error occurered in segment generation:{e}")

            return {}

    def generate_script(self, full_prompt, image, chat):

        try:
            response = chat.send_message_with_images(
                full_prompt, image, self.video_config.get("aspect_ratio", "")
            )

            script = UtilityTools.exract_text_from_chat_response(response)

            if not script or not script.strip():
                raise ValueError("No script generated")

            return script.strip()
        except Exception as e:
            print(f"Error occurered in script generation:{e}")

            return ""

    def generate_image(
        self,
        prompt,
        image_list,
        base_prompt_key,
        chat,
        image_generator,
        agent_config,
        segment_index,
    ):

        image_path = image_generator.create_image(
            image_list=image_list,
            prompt=prompt,
            base_prompt_key=base_prompt_key,
            chat=chat,
            agent_config=agent_config,
            segment_index=segment_index,
        )

        return image_path

    def validate_segment_list(self, segment_list):
        if not ValidationTools.validate_segment_key_values(segment_list):
            print("Invalid segment key values")
            return False

        if not ValidationTools.validate_segment_duration(
            segment_list, self.video_config.get("duration", 25)
        ):
            print("Invalid segment duration")
            return False

        return True


    def validate_video_require_human_or_not(self):

        user_description = self.request_data.get("video_description")
        system_description = self.request_data.get("description")

        prompt = generate_human_check_prompt(system_description, user_description)
        client = CustomOpenAIClient()
        response = client.call_open_ai({"prompt_text": prompt})

        return response == "Yes"

    def set_data_for_video_script(self, video_config, prompt):
        content_kit = self.message.get("content_kit", {})
        human_kit = self.message.get("human_kit", {})

        if not human_kit:
            human_kit = {}

        region = content_kit.get("region")
        human_kit["region"] = region

        is_human_required = self.validate_video_require_human_or_not()

        print(f"{is_human_required = }")

        if is_human_required:
            
            user_params =  generate_human_parameters_section(
            human_kit.get("user_params", {})
            )
        else:
            user_params = (
                "Do not include any people, humans, faces, or body parts in the visuals. "
                "All keyframes should focus solely on products, environments, and objects. "
                "Scenes should feel real but entirely unpopulated by humans."
            )

        brand_voice = generate_brand_voice_section(content_kit.get("brand_voice", {}))

        video_config["user_params"] = user_params
        video_config["brand_voice"] = brand_voice

        # Updating prompt with variables in video_config
        self.script_generator_system_prompt = (
            self.script_generator_system_prompt.format(**video_config)
        )

        full_script_prompt = (
            f"{self.script_generator_system_prompt}\nUser idea: {prompt}"
        )

        print(f"{self.request_data.get('video_description') = }")

        if self.request_data.get("video_description"):
            full_script_prompt = f"{full_script_prompt}\n Video Requirements: {self.request_data.get('video_description')}"

        return full_script_prompt

    def set_data_for_script_analyzer(self):
        self.script_analyzer_system_prompt = self.script_analyzer_system_prompt.format(
            **self.video_config
        )

        full_script_analyzer_prompt = f"{self.script_analyzer_system_prompt}\n{self.script_analyzer_output_format}\nSCRIPT:\n{self.script}\n PRODUCT_DESCRIPTION:{self.product_description}"
        # full_script_analyzer_prompt = generate_keyframe_prompt(
        #     self.video_config.get('duration'),
        #     self.video_config.get('brand_voice'),
        #     self.video_config.get('user_params'),
        #     self.script

        #     )
        return full_script_analyzer_prompt

    def analyze_script(self, full_script_analyzer_prompt, product_image):
        """
        Analyze a given script and generate validated segments using the full_script_analyzer_prompt and product image.
        Retries up to 3 times if invalid segments are produced.
        """
        try:
            valid_segment_list = False
            retry_counter = 0

            # print("INFO: Starting script analysis")
            # print(f"DEBUG: Analyzer prompt: {full_script_analyzer_prompt[:100]}...")
            # print(f"DEBUG: Product image: {product_image}")

            while not valid_segment_list and retry_counter < 3:
                print(
                    f"INFO: Attempt {retry_counter + 1} - Generating segments from script..."
                )

                segment_json_object = self.generate_segments_from_script(
                    [full_script_analyzer_prompt], [product_image], self.chat_script
                )

                #print(f"DEBUG: Raw segment JSON object: {segment_json_object}")

                segment_list = UtilityTools.parse_json_response(segment_json_object)
                #print(f"DEBUG: Parsed segment list: {segment_list}")

                if not segment_list:
                    print("WARNING: No segments found in parsed response.")
                    return None

                if not self.validate_segment_list(segment_list):
                    retry_counter += 1
                    print(
                        f"WARNING: Invalid segment list detected. Attempt {retry_counter}/3"
                    )

                    if retry_counter < 3:
                        print("INFO: Retrying script analysis...")
                    valid_segment_list = False
                else:
                    print("INFO: Valid segment list found successfully.")
                    valid_segment_list = True

                    return segment_list

            print("ERROR: Failed to obtain a valid segment list after 3 retries.")
            return None

        except Exception as e:
            print(f"ERROR: Exception occurred during script analysis: {e}")
            import traceback

            print(traceback.format_exc())
            return None


    def get_keyframe_url_from_bytes(self, file_bytes, index):
        object_name = (
                f"{VIDEO_BASE_PATH}/{self.message.get('generated_post_id')}/key_frames"
                )

        bytes_dict = {
                "fname": f"{index}_{int(time.time())}.png",
                "file_bytes": file_bytes,
            }

        keyframe_s3_url = self.upload_file_in_s3(
                    bytes_dict, object_name, content_type="image/png"
                )

        return keyframe_s3_url


    def notify_keyframe_issue(self, stage, segment_index, attempt, max_attempts, prev_keyframe_url, next_or_regen_url, validated_data):

        # Identify failure stage label
        post_id = self.message.get("generated_post_id")

        stage_label = (
            f"⚠️ Keyframe Validation Failed (`{post_id}`)"
            if stage == "validation"
            else f"❌ Keyframe Regeneration Failed (`{post_id}`)"
        )
                # Build Slack message

        validator_result = ""

        if validated_data:
            for key, value in validated_data.items():

                pretty_key = key.replace("_", " ").title()

                # Format dicts/lists cleanly
                if isinstance(value, dict):
                    value_str = json.dumps(value, indent=2)
                elif isinstance(value, list):
                    value_str = "\n".join([f"- {item}" for item in value])
                else:
                    value_str = str(value)

                validator_result += f"*{pretty_key}:*\n{value_str}\n\n"
        else:
            validator_result = "_No validator details returned._\n\n"


        slack_msg = (
            f"*{stage_label}*\n"
            f"*Post ID:* `{post_id}`\n"
            f"*Segment:* `{segment_index}`\n"
            f"*Attempt:* `{attempt}/{max_attempts}`\n\n"
            f"*Previous Keyframe URL:*\n{prev_keyframe_url}\n\n"
            f"*Attempted Frame URL:*\n{next_or_regen_url}\n\n"
            f"*Validation Result:*\n{validator_result}"
        )
       
        try:
            send_slack_message(slack_msg)
        except Exception as e:
            print(f"Slack error: {e}")
    
    def validate_and_regenerate_scene(self, product_image_pil, prev_image_pil, prev_keyframe_url, new_image_path, segment_index, image_list, segment_prompt):

        next_bytes = new_image_path.image_bytes
        next_frame_pil = Image.open(io.BytesIO(next_bytes))

        
        next_keyframe_url = self.get_keyframe_url_from_bytes(next_bytes, segment_index)

        print("\n------------------------------------------------")
        print(f"🔎 VALIDATION START: Segment #{segment_index}")
        print(f"Prev keyframe URL: {prev_keyframe_url}")
        print(f"Next keyframe URL: {next_keyframe_url}")
        print("------------------------------------------------\n")

        if prev_image_pil is None:
            print("➡️ First keyframe — skipping validation.")
            return new_image_path, next_frame_pil, next_keyframe_url

        # Build LLM prompt
        prompt = generate_product_scene_validation_prompt()

        MAX_VALIDATION_ATTEMPTS = 1
        MAX_REGEN_ATTEMPTS = 1

        # ---------------------------
        # MAIN VALIDATION LOOP (3x)
        # ---------------------------
        last_failure_reason = ""
        fix_suggestions = ""

        for v_attempt in range(1, MAX_VALIDATION_ATTEMPTS + 1):

            print(f"\n🔍 Validation Attempt {v_attempt}/{MAX_VALIDATION_ATTEMPTS}")
            print(f"Prev URL: {prev_keyframe_url}")
            print(f"Next URL: {next_keyframe_url}")
            

            # Send validation prompt with 3 images
            response = self.chat_script.send_message_with_images(
                [prompt],
                [prev_image_pil, next_frame_pil],
                aspect_ratio=self.video_config.get("aspect_ratio")
            )

            raw_json = UtilityTools.exract_text_from_chat_response(response)
            validated_data = parse_json_from_markdown(raw_json)

            print(f"Validation JSON: {validated_data}")

            if validated_data:
                continuation_ok = validated_data.get("is_valid_continuation", False)

                if not continuation_ok:
                    last_failure_reason = validated_data.get('reason')
                    fix_suggestions = validated_data.get("fix_suggestion")
                    self.notify_keyframe_issue(
                        stage="validation",
                        segment_index=segment_index,
                        attempt=v_attempt,
                        max_attempts=MAX_VALIDATION_ATTEMPTS,
                        prev_keyframe_url=prev_keyframe_url,
                        next_or_regen_url=next_keyframe_url,
                        validated_data=validated_data
                    )
            else:
                print(" Invalid JSON returned → treating as FAIL.")
                continuation_ok = False

            # SUCCESS → return
            if continuation_ok:
                print(" Validation PASSED. Keyframe accepted.")
                return new_image_path, next_frame_pil, next_keyframe_url

            # FAILED → regen
            print(" Validation FAILED → starting regeneration attempts...\n")

            # -------------------------------------------------
            # REGENERATION LOOP (3x)
            # -------------------------------------------------
            for r_attempt in range(1, MAX_REGEN_ATTEMPTS + 1):

                print(f"     Regeneration Attempt {r_attempt}/{MAX_REGEN_ATTEMPTS}")

                regen_image_list = [
                    image_list[1],
                    next_frame_pil,
                    product_image_pil
                ]

                
                regeneration_prompt = build_regeneration_prompt(segment_prompt, last_failure_reason, fix_suggestions)
                response = self.chat_image.send_message_with_images([regeneration_prompt], regen_image_list, self.video_config.get('aspect_ratio'))
                regeneration_prompt = UtilityTools.exract_text_from_chat_response(response)
                new_keyframe_creation_prompt = f"{regeneration_prompt}. Generate a new correct keyframe image based on the above given instructions.The first image attached is the product image and second is previous keyframe image"

                print(f"{new_keyframe_creation_prompt = }")
                
                # Generate new keyframe
                regenerated_path = self.generate_image(
                    new_keyframe_creation_prompt,
                    [product_image_pil, regen_image_list[0]],
                    "direct_single_image_generation",
                    self.chat_image,
                    self.image_generator,
                    self.agent_prompt_config,
                    segment_index,
                )

                regenerated_bytes = regenerated_path.image_bytes
                regenerated_pil = Image.open(io.BytesIO(regenerated_bytes))

                regenerated_url = self.get_keyframe_url_from_bytes(
                    regenerated_bytes, segment_index
                )

                print(f"     Regenerated keyframe URL: {regenerated_url}")

                # Validate regenerated frame
                response = self.chat_script.send_message_with_images(
                    [prompt],
                    [prev_image_pil, regenerated_pil],
                    aspect_ratio=self.video_config.get("aspect_ratio")
                )

                raw_re_json = UtilityTools.exract_text_from_chat_response(response)
                re_val = parse_json_from_markdown(raw_re_json)

                print(f"    Regeneration Validation JSON: {re_val}")

                if not re_val:
                    print("     Invalid regeneration JSON → FAIL")
                    continue

                r_continuation_ok = re_val.get("is_valid_continuation", False)

                if r_continuation_ok:
                    print("    Regenerated keyframe VALID → Using this frame.")
                    return regenerated_path, regenerated_pil, regenerated_url

                else:
                    last_failure_reason = re_val.get("reason")
                    fix_suggestions = re_val.get("fix_suggestions")
                    
                    self.notify_keyframe_issue(
                        stage="regeneration",
                        segment_index=segment_index,
                        attempt=r_attempt,
                        max_attempts=MAX_REGEN_ATTEMPTS,
                        prev_keyframe_url=prev_keyframe_url,
                        next_or_regen_url=regenerated_url,
                        validated_data=re_val
                    )

                print("    Regenerated keyframe still invalid.")

            # All 3 regen attempts failed
            print(f" All {MAX_REGEN_ATTEMPTS} regeneration attempts FAILED for this cycle.")

        # All validation cycles failed
        print(f"\n ERROR: Keyframe rejected after {MAX_REGEN_ATTEMPTS} validations & {MAX_REGEN_ATTEMPTS} regenerations.")
        
        return regenerated_path, regenerated_pil, regenerated_url
    
    def compute_keyframes(self, segment_list, product_image):
        keyframe_image_list = []
        image_path = None
        prev_keyframe_pil = None
        prev_keyframe_url = ""

        try:
            image_list = [product_image]
            
            for segment_index, segment in enumerate(segment_list):
                print(f"\n\nSegment prompt: {segment['keyframe_prompt']}")

                if segment_index and image_path and image_path.image_bytes:
                    image_list = [
                        product_image,
                        prev_keyframe_pil,
                    ]
                # Check if segment duration is even and add 1 if not
                segment_duration = int(segment["video_segment_duration"])
                keyframe_prompt = segment["keyframe_prompt"]

                if segment_duration % 2 == 1:
                    segment_duration += 1
                    segment["video_segment_duration"] = segment_duration

                new_image_path = self.generate_image(
                    keyframe_prompt,
                    image_list,
                    "direct_single_image_generation",
                    self.chat_image,
                    self.image_generator,
                    self.agent_prompt_config,
                    segment_index,
                )

                next_keyframe_pil = Image.open(io.BytesIO(new_image_path.image_bytes))
                next_keyframe_url = self.get_keyframe_url_from_bytes(new_image_path.image_bytes, segment_index)

                # new_image_path, next_keyframe_pil, next_keyframe_url = self.validate_and_regenerate_scene(
                #     product_image,
                #     prev_keyframe_pil,
                #     prev_keyframe_url,
                #     new_image_path,
                #     segment_index,
                #     image_list,
                #     segment['keyframe_prompt']
                # )

                prev_keyframe_pil = next_keyframe_pil
                prev_keyframe_url = next_keyframe_url
                image_path = new_image_path

                keyframe_image_list.append({
                    "keyframe_image": image_path,
                    "keyframe_s3_url": next_keyframe_url,
                    "segment_video_prompt": segment["segment_video_prompt"],
                    "keyframe_image_pil": next_keyframe_pil

                })
                
            return keyframe_image_list

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error Occured in computing keyframes: {e}")
            return None

    def modify_keyframe_prompts_for_keyframe_generation(self, keyframe_list, product_image):


        prev_updated_image_pil = keyframe_list[0].get("keyframe_image_pil")
        first_frame_url = keyframe_list[0].get("keyframe_s3_url")
        first_frame_google_image = keyframe_list[0].get("keyframe_image")

        for index, keyframe in enumerate(keyframe_list):
            is_first = index == 0
            is_last = index == len(keyframe_list) - 1

            if is_first:
                # First keyframe stays unchanged but becomes prev for next keyframe
                prev_updated_image_pil = keyframe["keyframe_image_pil"]
                prompt = update_keyframe_prompt_for_first_video_generation(keyframe["segment_video_prompt"])
                response = self.chat_script.send_message_with_images(
                    [prompt],
                    [prev_updated_image_pil, product_image],
                    self.video_config.get("aspect_ratio")
                )
                updated_keyframe_prompt = UtilityTools.exract_text_from_chat_response(response)
                response = self.chat_image.send_message_with_images(
                [updated_keyframe_prompt],
                [product_image, prev_updated_image_pil],
                self.video_config.get("aspect_ratio")
                )
                updated_image = UtilityTools.extract_image_from_chat_response(response)
                updated_keyframe_pil = Image.open(io.BytesIO(updated_image.image_bytes))
                updated_keyframe_url = self.get_keyframe_url_from_bytes(updated_image.image_bytes, index)
                keyframe.update({
                    "updated_keyframe_s3_url": updated_keyframe_url,
                    "updated_keyframe_prompt": updated_keyframe_prompt,
                    "updated_keyframe_pil": updated_keyframe_pil,
                    "updated_keyframe_image": updated_image,

                    "first_frame": first_frame_url,
                    "last_frame": updated_keyframe_url,
                    "first_frame_google_obj": first_frame_google_image,
                    "last_frame_google_obj": updated_image,
                })
                first_frame_url = updated_keyframe_url
                prev_updated_image_pil = updated_keyframe_pil
                first_frame_google_image = updated_image
                
                continue

            # PREV IMAGE LOGIC (THIS IS THE FIX)
            prev_image = prev_updated_image_pil  # <-- now using updated previous keyframe
            curr_image = keyframe["keyframe_image_pil"]

            # PROMPT SELECTION
            segment_video_prompt = keyframe["segment_video_prompt"]

            if not is_last:
                prompt = update_keyframe_prompt_for_middle_video_generation(segment_video_prompt)
            else:
                prompt = update_keyframe_prompt_for_end_video_generation(segment_video_prompt)

            # STEP 1: UPDATE PROMPT
            response = self.chat_script.send_message_with_images(
                [prompt],
                [prev_image, curr_image, product_image] if not is_last else [prev_image, product_image],
                self.video_config.get("aspect_ratio")
            )
            updated_keyframe_prompt = UtilityTools.exract_text_from_chat_response(response)

            # STEP 2: UPDATE IMAGE
            response = self.chat_image.send_message_with_images(
                [updated_keyframe_prompt],
                [product_image, prev_image],
                self.video_config.get("aspect_ratio")
            )

            updated_image = UtilityTools.extract_image_from_chat_response(response)
            updated_keyframe_pil = Image.open(io.BytesIO(updated_image.image_bytes))
            updated_keyframe_url = self.get_keyframe_url_from_bytes(updated_image.image_bytes, index)

            # SAVE UPDATE
            keyframe.update({
                "updated_keyframe_s3_url": updated_keyframe_url,
                "updated_keyframe_prompt": updated_keyframe_prompt,
                "updated_keyframe_pil": updated_keyframe_pil,
                "updated_keyframe_image": updated_image,

                "first_frame": first_frame_url,
                "last_frame": updated_keyframe_url,
                "first_frame_google_obj": first_frame_google_image,
                "last_frame_google_obj": updated_image,
            })

            first_frame_url = updated_keyframe_url
            prev_updated_image_pil = updated_keyframe_pil
            first_frame_google_image = updated_image


        return keyframe_list

    def set_post_title_caption(self, script):
        prompt = create_prompt_for_post_and_caption(script)
        client = CustomOpenAIClient()
        response = client.call_open_ai({"prompt_text": prompt})

        self.post_title = response

    def set_summary_for_video(self, script):
        prompt = create_prompt_for_summary_generation(script)
        client = CustomOpenAIClient()
        response = client.call_open_ai({"prompt_text": prompt})

        self.summary = response

    def upload_file_in_s3(self, byte_dict, file_object_name, content_type="video/mp4"):

        s3_url = ""

        fname = byte_dict.get("fname")
        file_bytes = byte_dict.get("file_bytes")

        if not fname or not file_bytes:
            print("No filename or file bytes  provided in byte_dict. Skipping upload.")
            return s3_url

        object_name = f"{file_object_name}/{fname}"
        print(f"Uploading '{fname}' to S3 bucket '{self.bucket}' at 'https://{self.bucket}.s3.amazonaws.com/{object_name}'...")

        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=object_name,
                Body=file_bytes,
                ContentType=content_type,
            )
            s3_url = f"https://{self.bucket}.s3.amazonaws.com/{object_name}"

        except Exception as e:
            print(f"Failed to upload '{fname}' to S3. Error: {e}")

        return s3_url

    def get_keyframes_and_images_for_video_creation(self, keyframe_image_list, segment_list):
        video_request_json_list = []
        key_frame_json_list = []

        set_resolution = False

        for index, keyframe_dict in enumerate(keyframe_image_list):
            segment = segment_list[index]

            if keyframe_dict.get("updated_keyframe_image"):
                keyframe_obj = keyframe_dict["updated_keyframe_image"]
                keyframe_s3_url = keyframe_dict["updated_keyframe_s3_url"]
                prev_keyframe_s3_url = keyframe_dict["keyframe_s3_url"]
                updated_keyframe_prompt = keyframe_dict["updated_keyframe_prompt"]
            else:
                keyframe_obj = keyframe_dict["keyframe_image"]
                keyframe_s3_url = keyframe_dict["keyframe_s3_url"]
                prev_keyframe_s3_url = ""
                updated_keyframe_prompt = ""

            video_request_json = {
                "prompt": segment.get("segment_video_prompt"),
                "segment_index": segment.get("keyframe_number"),
                "first_frame": keyframe_dict["first_frame_google_obj"],
                "aspect_ratio": self.video_config["aspect_ratio"],
                "segment_duration": segment.get("video_segment_duration"),
                "gemini_api_key": self.gemini_video_api_key,
                "last_frame": keyframe_dict["last_frame_google_obj"]
            }

            # Add next keyframe as last_frame (except last segment)
            # if index < len(keyframe_image_list) - 1:

            #     next_frame_dict = keyframe_image_list[index + 1]
            #     next_keyframe_obj = (
            #         next_frame_dict.get("updated_keyframe_image") 
            #         or next_frame_dict.get("keyframe_image")
            #     )
                            
            #     video_request_json["last_frame"] = next_keyframe_obj
            # else:
            #     video_request_json["last_frame"] = "final_segment"

            # Store S3 URL back into the segment metadata
            segment.update({
                "updated_keyframe_prompt":updated_keyframe_prompt,
                "prev_generated_keyframe_url":prev_keyframe_s3_url,
                "keyframe_s3_url":keyframe_s3_url,
                "first_frame":keyframe_dict.get("first_frame"),
                "last_frame": keyframe_dict.get("last_frame")

            })


            # Extract resolution once (from first keyframe)
            if not set_resolution:
                first_frame_bytes = keyframe_obj.image_bytes
                pil_img = Image.open(io.BytesIO(first_frame_bytes))
                self.resolution = list(pil_img.size)
                print(f"{self.resolution = }")

                self.thumbnail = keyframe_s3_url
                set_resolution = True

            video_request_json_list.append(video_request_json)
            key_frame_json_list.append(segment)

        return video_request_json_list, key_frame_json_list

    def get_video_chunks_list(self, video_request_json_list, key_frame_json_list):
        s3_urls = []
        object_name = (
            f"{VIDEO_BASE_PATH}/{self.message.get('generated_post_id')}/chunks"
        )

        for i, video_request in enumerate(video_request_json_list):
            bytes_dict = generate_video(video_request)
            s3_url = self.upload_file_in_s3(
                bytes_dict, object_name, content_type="video/mp4"
            )

            if not s3_url:
                print(f"s3 url not generated for {bytes_dict.get('fname')}")
                key_frame_json_list[i]["video_url"] = ""
                continue

            # Add video_url to corresponding keyframe dict
            key_frame_json_list[i]["video_url"] = s3_url

            s3_urls.append(s3_url)

        return s3_urls


    def add_frame_links_for_metadata(self, keyframe_list):

        for i, item in enumerate(keyframe_list):
            item["first_frame"] = item.get("keyframe_s3_url")

            if i < len(keyframe_list) - 1:
                item["last_frame"] = keyframe_list[i + 1].get("keyframe_s3_url")
            else:
                item["last_frame"] = ""

        return keyframe_list


    def compute(self):

        asset_base64 = self.request_data.get("asset_base64")

        print("=== [compute] Starting image + script generation ===")

        # --- Step 1: Check what we got ---
        if not asset_base64:
            print("[ERROR] asset_base64 is empty or None")

        # --- Step 2: Try image creation ---
        try:
            image = AssetProcessor.get_image_from_base64(asset_base64)
            # print("[DEBUG] Successfully created Image object from base64")
            # print(
            #     f"[DEBUG] Image format: {getattr(image, 'format', 'unknown')}, size: {getattr(image, 'size', 'unknown')}"
            # )

        except Exception as e:
            print(f"[ERROR] Failed to create Image from base64: {e}")
            image = None
            raise RuntimeError(f"Failed to process image from base64 input") from e

        product_prompt = generate_prompt_for_product_description()
        response = self.chat_script.send_message_with_images([product_prompt], [image])
        self.product_description = UtilityTools.exract_text_from_chat_response(response)


        full_script_prompt = self.set_data_for_video_script(
            self.video_config, self.request_data.get("description")
        )

        full_script_prompt = f"{full_script_prompt}\n Product Description(To be taken into consideration while generation):\n{self.product_description}"
        
        self.script = self.generate_script(
            [full_script_prompt], [image], self.chat_script
        )

        print(f"{self.script = }")

        self.video_inputs = {
            "script_input": full_script_prompt,
            "script_output": self.script,
        }

        if not self.script:
            raise RuntimeError("No script generated")



        print(f"{self.product_description = }")


        full_script_analyzer_prompt = self.set_data_for_script_analyzer()

        # print(f"{full_script_analyzer_prompt = }")

        segment_list = self.analyze_script(full_script_analyzer_prompt, image)

        self.video_inputs.update({"segment_list_prompt": full_script_analyzer_prompt})

        if not segment_list:
            raise RuntimeError("No segments found")

        keyframe_image_list = self.compute_keyframes(segment_list, image)

        if not keyframe_image_list:
            raise RuntimeError("No keyframes generated")
            
        keyframe_image_list = self.modify_keyframe_prompts_for_keyframe_generation(keyframe_image_list, image)

        print(f"{keyframe_image_list = }")

        #video request json generation
        video_request_json_list, key_frame_json_list = (
            self.get_keyframes_and_images_for_video_creation(
                keyframe_image_list, segment_list
            )
        )

        #key_frame_json_list = self.add_frame_links_for_metadata(key_frame_json_list)

        print(f"{key_frame_json_list = }")

        s3_urls = self.get_video_chunks_list(
            video_request_json_list, key_frame_json_list
        )


        self.keyframe_metadata = key_frame_json_list

        object_name = f"{VIDEO_BASE_PATH}/{self.message.get('generated_post_id')}"
        merged_url = merge_videos_with_mediaconvert(
            s3_urls,
            self.bucket,
            output_key_prefix=object_name,
            role_arn="arn:aws:iam::506569801059:role/media-convert",
        )


        # ffmpeg_path = "/var/task/ffmpeg/ffmpeg"
        # ffprobe_path = "/var/task/ffmpeg/ffprobe"
        # merged_video = merge_s3_videos_crossfade_noaudio(s3_urls, ffmpeg_path=ffmpeg_path, ffprobe_path=ffprobe_path)
        # output_filename = f"merged_{int(time.time())}.mp4"
        # merged_url = self.upload_file_in_s3({"file_bytes": merged_video, "fname": output_filename}, object_name)

        print(f"{merged_url = }")

        self.set_post_title_caption(self.script)
        self.set_summary_for_video(self.script)

        return f"{merged_url}"

    def set_request_data_to_process(self):

        #print("=== [set_request_data_to_process] Starting ===")

        items = self.message.get("items", [{}])[0]
        description = self.message.get("content_pillar", {}).get("description")
        asset_url_list = items.get("assets", [])
        metadata = items.get("metadata", {})
        video_description = items.get("descriptions", [{}])[0].get("description")

        asset_url = asset_url_list[0] if len(asset_url_list) else ""
        #print(f"[DEBUG] Asset URL: {asset_url}")

        try:
            bg_removed = AssetProcessor.extract_bg_removed_asset(asset_url)
            print(f"[DEBUG] Background removed asset: {bg_removed}")
        except Exception as e:
            print(f"[ERROR] extract_bg_removed_asset() failed: {e}")
            bg_removed = asset_url

        self.video_config = {
            "duration": metadata.get("duration", 25),
            "aspect_ratio": metadata.get("aspect_ratio", "9:16"),
        }
        #print(f"[DEBUG] Video config: {self.video_config}")

        # Convert to base64
        try:
            asset_base64 = AssetProcessor.convert_asset_url_to_base64(bg_removed)
            print(f"[DEBUG] Base64 conversion success. Length: {len(asset_base64)}")

        except Exception as e:
            print(f"[ERROR] convert_asset_url_to_base64() failed: {e}")
            asset_base64 = ""

        self.image_generator = ImageGenerator(
            self.chat_image, self.video_config.get("aspect_ratio")
        )

        self.request_data = {
            "description": description,
            "asset_base64": asset_base64,
            "video_description": video_description,
        }

        print(f"[DEBUG] Description length: {len(description or '')}")
        print("=== [set_request_data_to_process] Completed ===\n")

    def process_s3_url_list(self, s3_url_list):

        entry = {
            "link": s3_url_list[0],
            "caption": "",
            "post_title": self.post_title,
            "resolution": self.resolution,
            "scores": {},
            "aspect_ratio": self.video_config.get("aspect_ratio", "9:16"),
            "thumbnail": self.thumbnail,
        }

        metadata = {}
        metadata["keyframe_metadata"] = self.keyframe_metadata
        metadata["summary"] = self.summary
        metadata["video_inputs"] = self.video_inputs

        return [entry], "", metadata

    def set_response_data_for_backend(self, s3_url_list):
        print("=== [set_response_data_for_backend] Starting ===")
        print(f"[DEBUG] Incoming S3 URL list: {s3_url_list}")

        response = {
            "generate_config": self.message.get("id"),
            "idea": "",
            "generated_content_description": [],
            "scheduled_at": 0,
            "brand_id": self.message.get("brand_id"),
            "status": "success",
            "caption": "",
            "generated_content_links": [],
        }
        print(f"[DEBUG] Initial response object: {response}")

        try:
            generated_content, caption, metadata = self.process_s3_url_list(s3_url_list)
            print(f"[DEBUG] Generated content: {generated_content}")
            print(f"[DEBUG] Caption: {caption}")
            print(f"[DEBUG] Metadata: {metadata}")
        except Exception as e:
            print(f"[ERROR] process_s3_url_list() failed: {e}")
            generated_content, caption, metadata = [], "", {}

        # Update response
        response["generated_content"] = generated_content
        response["caption"] = caption
        response["metadata"] = metadata

        if self.message.get("generated_post_id"):
            response["generated_post_id"] = self.message["generated_post_id"]
            print(f"[DEBUG] Added generated_post_id: {response['generated_post_id']}")

        print(f"[DEBUG] Final response object: {response}")
        print("=== [set_response_data_for_backend] Completed ===\n")

        return response

    def process_message(self, message):
        self.message = message
        self.set_request_data_to_process()

        try:

            s3_url = self.compute()
            print(f"{s3_url=}")
            response = self.set_response_data_for_backend([s3_url])

            return {"success": True, "output_format": response}

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error Occured: {e}")
            return {"success": False, "error_message": str(e)}


if __name__ == "__main__":

    with open(
        "data.json", "r", encoding="utf-8"
    ) as f:
        data = json.load(f)

    video_generator = VideoGenerator()
    start_time = time.time()
    response = video_generator.process_message(data)
    end_time = time.time()

    print(f"{response = }")

    print(f"Time to process video creation-{end_time-start_time}")
