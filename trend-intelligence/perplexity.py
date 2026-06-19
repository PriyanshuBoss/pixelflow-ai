import json
import re
import time
import os
from datetime import datetime
from html import unescape
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

from constants import PERPLEXITY_CONFIG, PERPLEXITY_MODEL_CONFIG
from prompt_templates import prompt_template_for_perplexity_api


class TrendsInsightsPerplexityView:
    
    def __init__(self, input_data):
        self.input_data = input_data
        self.perplexity_config = self._set_perplexity_config()

        print(self.perplexity_config)


    def _set_perplexity_config(self):
        
        if self.input_data.get('ai_model'):
            ai_model = self.input_data.get('ai_model')
            ai_model_config = PERPLEXITY_MODEL_CONFIG.get(ai_model)

            if not ai_model_config:
                print(f"Model not found in perplexity:{ai_model}")
            
            return ai_model_config
        
        return PERPLEXITY_CONFIG
    
    def _create_prompt_for_trends(self, input_data):
        
        if input_data.get('prompt'):
            base_prompt = input_data.get('prompt')
        else:
            base_prompt = prompt_template_for_perplexity_api(input_data)
        
        return base_prompt
    
    def _extract_structured_insights(self, text):
        text = text.replace('```json\n', '').replace('\n```', '')
        
        # Look for JSON array structure
        json_match = re.search(r'\[\s*{.*?}\s*]', text, re.DOTALL)
        
        if not json_match:
            print("No JSON block found.")
            return None
        
        json_str = json_match.group(0)
        
        try:
            return json.loads(unescape(json_str))
        except json.JSONDecodeError as e:
            print("JSON parsing error:", e)
            return None
    

    @retry(
        stop=stop_after_attempt(3),  # 1 original + 2 retries
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    )
    def _perplexity_chat_execute(self, prompt):
        print("[_perplexity_chat_execute] Starting Perplexity API execution.")
        
        try:
            model = self.perplexity_config['model']
            max_tokens = self.perplexity_config['max_tokens']
            api_key = os.getenv('PERPLEXITY_API_KEY')
            
            print(f"[_perplexity_chat_execute] PERPLEXITY_CONFIG loaded: model={model}, max_tokens={max_tokens}")
            
            if not api_key:
                raise ValueError("PERPLEXITY_API_KEY environment variable is not set.")
            
            print("[_perplexity_chat_execute] API key successfully loaded.")
            
        except KeyError as e:
            print(f"[ERROR][_perplexity_chat_execute] Missing PERPLEXITY_CONFIG key: {e}")
            raise ValueError(f"Missing PERPLEXITY_CONFIG key: {e}")
        
        try:
            url = "https://api.perplexity.ai/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.0,
                "top_p": 0.9,
                "return_citations": True,
                "search_domain_filter": ["perplexity.ai"],
                "return_images": False,
                "return_related_questions": False,
                "search_recency_filter": "month",
                "top_k": 0,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 1
            }
            
            print(f"[_perplexity_chat_execute] Perplexity API request initialized at {datetime.now()}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            print(f"[_perplexity_chat_execute] Raw response status: {response.status_code}")
            print(f"[_perplexity_chat_execute] Request completed at {datetime.now()}")
            
            if response.status_code == 429:
                print("[ERROR][_perplexity_chat_execute] Rate limit exceeded.")
                raise requests.exceptions.RequestException("Rate limit exceeded for Perplexity API")
            
            if response.status_code != 200:
                print(f"[ERROR][_perplexity_chat_execute] HTTP error: {response.status_code}")
                print(f"[ERROR][_perplexity_chat_execute] Response: {response.text}")
                raise requests.exceptions.RequestException(f"HTTP {response.status_code}: {response.text}")
            
            response_data = response.json()
            print(f"[_perplexity_chat_execute] Raw response data: {response_data}")
            
            if not response_data.get('choices') or not response_data['choices']:
                print("[ERROR][_perplexity_chat_execute] Received empty or invalid response.")
                raise RuntimeError("Received empty or invalid response from Perplexity API.")
            
            text_content = response_data['choices'][0]['message']['content']
            
            if not text_content.strip():
                print("[ERROR][_perplexity_chat_execute] No text content found in response.")
                raise RuntimeError("Perplexity API returned no text content.")
            
            print(f"[_perplexity_chat_execute] Final text content: {text_content}")
            
            insights = self._extract_structured_insights(text_content)
            print(f"[_perplexity_chat_execute] Extracted insights: {insights}")
            
            return insights
            
        except requests.exceptions.ConnectionError as e:
            print(f"[ERROR][_perplexity_chat_execute] ConnectionError: {e}")
            raise ConnectionError(f"Failed to connect to Perplexity API: {e}")
        except requests.exceptions.Timeout as e:
            print(f"[ERROR][_perplexity_chat_execute] Timeout: {e}")
            raise RuntimeError(f"Request timeout for Perplexity API: {e}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR][_perplexity_chat_execute] RequestException: {e}")
            raise RuntimeError(f"Perplexity API error: {e}")
        except Exception as e:
            print(f"[ERROR][_perplexity_chat_execute] Unexpected error: {e}")
            raise RuntimeError(f"Unexpected error during Perplexity API execution: {e}")

    def generate_research_data(self):
        start_time = time.time()
        prompt = self._create_prompt_for_trends(self.input_data)
        research_data = self._perplexity_chat_execute(prompt)
        
        print(f"Research data: {research_data}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"Perplexity Research Report generated in {execution_time}")
        
        return {
            'info': research_data,
            'prompt': prompt,
            'ai_model': PERPLEXITY_CONFIG['model']
        }
