"""
NanaBananaChat: Conversational image editing using Gemini 2.5 Flash Image Preview
"""

import io
from typing import List, Optional
from google import genai
from PIL import Image, ImageFile

from common.utils import setup_logger


class NanaBananaChat:
    """Conversational image editing interface using Gemini 2.5 Flash Image Preview"""

    _chat_model = "gemini-2.5-flash-image"
    _llm_model = "gemini-2.5-flash"

    def __init__(self, api_key: str, image: Optional[ImageFile.ImageFile] = None):
        """Initialize chat with API key and starting image"""
        # Initialize client and load image
        self.logger = setup_logger(__name__)
        self.client = genai.Client(api_key=api_key)
        self.current_image = image
        self.temperature = 0.7
        self.max_output_tokens = 10000

        # Create chat session
        self.chat = self.client.chats.create(model=self._chat_model)
        self.logger.info("Successfully established chat context")

    def set_base(self, images: List[ImageFile.ImageFile], base_instruction: str) -> Exception:
        # Establish context with initial image
        self.current_image = images or self.current_image
        try:
            response = self.chat.send_message(self.current_image + [base_instruction])
            if not response or not response.text:
                raise Exception("Failed to establish chat context with initial image")
        except Exception as err:
            self.logger.error(f"Error while setting Inital Image {err = }")
            raise err

    def edit_image(self, prompt: str, aspect_ratio: str, request_payload=None) -> genai.types.Image:
        """Edit current image with natural language prompt"""
        if not prompt or not prompt.strip():
            raise ValueError("Edit prompt cannot be empty")

        self.logger.info(f"Processing edit request: {prompt}")
        images = []
        
        if request_payload:
            images = request_payload.get('images',[])

        try:
            # Send editing prompt to chat
            response = self.chat.send_message(
                [prompt]+images,
                config=genai.types.GenerateContentConfig(
                    image_config=genai.types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                    )
                ),
            )

            # Extract image from response
            new_image = self._extract_image_from_response(response)
            self.logger.info("Edit completed successfully")
            return new_image

        except Exception as e:
            self.logger.error(f"Image edit failed: {e}")
            raise Exception(f"Failed to edit image: {e}")

    def _extract_image_from_response(self, response) -> Image.Image:
        """Extract PIL Image from API response"""
        if not hasattr(response, "parts") or not response.parts:
            text_content = getattr(response, "text", "No text content")
            self.logger.error(f"No image parts in API response: {text_content}")
            raise Exception(
                f"API response contains no image parts. Response: {text_content}"
            )

        # Find image in response parts
        for part in response.parts:
            if hasattr(part, "as_image") and part.as_image():
                return part.as_image()

        self.logger.error("No image found in any response parts")
        raise Exception("No image found in API response")

    def call_llm(self, agent_name: str, prompt_parts: List, aspect_ratio: str = None):

        config = genai.types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens
        )
        response = self.client.models.generate_content(
            model=self._llm_model, contents=prompt_parts, config=config
        )

        if not response or not response.text:
            raise Exception(f"Empty response from {agent_name} agent")

        self.logger.info(f"Successfully received response from {agent_name} agent")
        self.logger.info(f"LLM response: {response.text}")
        return response.text
