import time
import anthropic
import re
import json
import re
import os
from datetime import datetime
from html import unescape
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


from constants import CLAUDE_CONFIG, CLAUDE_MODEL_CONFIG
from prompt_templates import generate_brand_analysis_prompt

class BrandKitAutomationClaudeView:
    
    def __init__(self, input_data):
        self.input_data = input_data
        self.claude_config = self._set_claude_config()
        print(self.claude_config)

    def _set_claude_config(self):
        
        if self.input_data.get('ai_model'):
            ai_model = self.input_data.get('ai_model')
            ai_model_config = CLAUDE_MODEL_CONFIG.get(ai_model)

            if not ai_model_config:
                print(f"Model not found in claude:{ai_model}")
            
            return ai_model_config
        
        return CLAUDE_CONFIG
    
    def _create_prompt(self, input_data):

        if input_data.get('prompt'):
            base_prompt = input_data.get('prompt')
        else:
            base_prompt = generate_brand_analysis_prompt(input_data)

        return base_prompt
    
    def _extract_format(self,raw):
        try:
            # Extract the JSON substring
            start = raw.find('{')
            end = raw.rfind('}') + 1
            json_str = raw[start:end]

            # Remove <cite ...>...</cite> tags
            json_str = re.sub(r'<cite[^>]*>(.*?)<\/cite>', r'\1', json_str)

            # Remove trailing commas before closing brackets
            json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)

            # Parse JSON string
            data = json.loads(json_str)
            return data
        except Exception as e:
            print("Failed to parse JSON:", e)
            return None

        # Print nicely
       

    @retry(
    stop=stop_after_attempt(3),  # 1 original + 2 retries
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((anthropic.APIConnectionError, anthropic.RateLimitError))
    )
    def _claude_chat_execute(self, prompt):
        print("[_claude_chat_execute] Starting Claude API execution.")

        try:
            model = self.claude_config['model']
            max_tokens = self.claude_config['max_tokens']
            max_uses = self.claude_config['max_uses']
            api_key = os.getenv('CLAUDE_API_KEY')

            print(f"[_claude_chat_execute] CLAUDE_CONFIG loaded: model={model}, max_tokens={max_tokens}, max_uses={max_uses}")
            
            if not api_key:
                raise ValueError("CLAUDE_API_KEY environment variable is not set.")
            
            print("[_claude_chat_execute] API key successfully loaded.")

        except KeyError as e:
            print(f"[ERROR][_claude_chat_execute] Missing CLAUDE_CONFIG key: {e}")
            raise ValueError(f"Missing CLAUDE_CONFIG key: {e}")

        try:
            client = anthropic.Anthropic(api_key=api_key)
            print(f"[_claude_chat_execute] Claude client initialized. at {datetime.now()}")

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": max_uses
                }]
            )

            print(f"[_claude_chat_execute] Raw response: {response}")
            print(f"[_claude_chat_execute] Request completed at {datetime.now()}" )

            if not hasattr(response, 'content') or not response.content:
                print("[ERROR][_claude_chat_execute] Received empty or invalid response.")
                raise RuntimeError("Received empty or invalid response from Claude API.")

            text_content = ""
            
            for content_block in response.content:
                print(f"[_claude_chat_execute] Processing content block: {content_block}")
                
                if content_block.type == "text":
                    text_content += content_block.text

            if not text_content.strip():
                print("[ERROR][_claude_chat_execute] No text content found in response.")
                raise RuntimeError("Claude API returned no text content.")

            print(f"[_claude_chat_execute] Final text content: {text_content}")

            insights = self._extract_format(text_content)
            print(f"[_claude_chat_execute] Extracted insights: {insights}")

            return insights

        except anthropic.APIConnectionError as e:
            print(f"[ERROR][_claude_chat_execute] APIConnectionError: {e}")
            raise ConnectionError(f"Failed to connect to Claude API: {e}")
        except anthropic.RateLimitError as e:
            print(f"[ERROR][_claude_chat_execute] RateLimitError: {e}")
            raise RuntimeError(f"Rate limit exceeded for Claude API: {e}")
        except anthropic.AnthropicError as e:
            print(f"[ERROR][_claude_chat_execute] AnthropicError: {e}")
            raise RuntimeError(f"Claude API error: {e}")
        except Exception as e:
            print(f"[ERROR][_claude_chat_execute] Unexpected error: {e}")
            raise RuntimeError(f"Unexpected error during Claude API execution: {e}")

        

    def generate_research_data(self):
        start_time = time.time()
        prompt = self._create_prompt(self.input_data)
        research_data = self._claude_chat_execute(prompt)
        
        print(f"Research data: {research_data}")
        
        end_time = time.time()

        execution_time = end_time-start_time

        print(f"Claude Research Report generated in {execution_time}")


        return {
            'info':research_data,
            'prompt':prompt,
            'ai_model': CLAUDE_CONFIG['model']
        }

