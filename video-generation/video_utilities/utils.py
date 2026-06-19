import json
import os
import re


class UtilityTools:

    @staticmethod
    def extract_image_from_chat_response(response):
        # Find image in response parts
        for part in response.parts:
            if hasattr(part, "as_image") and part.as_image():
                return part.as_image()

        return None

    @staticmethod
    def exract_text_from_chat_response(response):
        
        for part in response.parts:
            text_content = getattr(part, "text", "No text content")
            
            if text_content == "No text content":
                return None

        return response.text

    @staticmethod
    def save_image_and_prompt_locally(
        image, prompt, output_dir_path, image_name, prompt_name
    ):
        image_path = os.path.join(output_dir_path, image_name)
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)

        with open(os.path.join(output_dir_path, prompt_name), "w") as f:
            f.write(prompt)

        image.save(image_path)
        return image_path

    @staticmethod
    def parse_json_response(response_text: str):
        """Parse JSON response from LLM, extracting JSON from text if needed"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Check for markdown code blocks first
            markdown_match = re.search(
                r"```(?:json)?\s*(\[.*\]|\{.*\})\s*```", response_text, re.DOTALL
            )
            if markdown_match:
                try:
                    return json.loads(markdown_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Fall back to simple JSON object extraction
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    return {}

