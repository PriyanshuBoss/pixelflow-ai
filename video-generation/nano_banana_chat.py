from typing import List

from google import genai
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_sleep


def print_retry_details(retry_state):
    """Custom Tenacity hook to print retry info to console."""
    attempt = retry_state.attempt_number
    exception = retry_state.outcome.exception() if retry_state.outcome else None
    
    print(f"Retry attempt {attempt} failed due to: {exception}. Retrying...")



class NanoBananaChat:

    def __init__(
        self,
        api_key: str,
    ):
        try:
            self.client = genai.Client(api_key=api_key)

            self.chat = self.client.chats.create(model="gemini-2.5-flash-image")

        except Exception as e:
            print(f"Failed to initialize NanaBananaChat: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(Exception),
        before_sleep=print_retry_details,
        reraise=True
    )
    def send_message_with_images(self, text: list, images: list, aspect_ratio: str = None):
        """
        Send text + images to Gemini and return text-only output.
        Automatically retries on transient errors using Tenacity.
        """
        image_config = None
        
        if aspect_ratio:
            #print(f"{aspect_ratio = }")
            image_config = genai.types.ImageConfig(aspect_ratio=aspect_ratio)

        config = genai.types.GenerateContentConfig(
            image_config=image_config
        )

        message_parts = text + images

        #print("Sending message with images...")
        response = self.chat.send_message(message_parts, config=config)
        
        if not response or not getattr(response, "parts", None):
            raise ValueError("Empty or invalid response from Gemini API")

        #print(" Message sent successfully.")
        
        return response

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(Exception),
        before_sleep=print_retry_details,
        reraise=True
    )
    def send_message_with_text_only(self, text):
        """
        Send text-only input to Gemini with retry support.
        Automatically retries on transient errors (e.g. network issues, API timeouts).
        """
        print("Sending text-only message to Gemini...")

        response = self.chat.send_message(text)

        if not response or not getattr(response, "parts", None):
            raise ValueError("Empty or invalid response from Gemini API")

        print("Message sent successfully.")
        
        return response
