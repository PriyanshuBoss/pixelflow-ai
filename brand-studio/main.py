
import json
import os
import re
import uuid
from brand_fetch_api import BrandFetchApi
from claude import BrandKitAutomationClaudeView
from common.nano_banana_client import NanaBananaChat
from common.utils import send_slack_message
from prompt_templates import generate_brand_analysis_prompt, generate_user_params_prompt_using_brand_configuration

class BrandKitAutomater:
  
    def __init__(self):
        self.client = NanaBananaChat(os.getenv('GEMINI_API_KEY'))

    def _create_response_format(self, brand_data):
        output_format = brand_data.copy()
        output_format.update(brand_data)

        return output_format

    def _infer_human_parameters_from_brand_data(self, brand_config):
        prompt = generate_user_params_prompt_using_brand_configuration(brand_config)

        llm_response = self.client.call_llm("user-profile-agent", [prompt])

        try:
            clean_response = re.sub(r"^```(?:json)?|```$", "", llm_response, flags=re.MULTILINE).strip()
            user_params_json = json.loads(clean_response)

        except Exception as e:
            print(f"Error fetching user params={e}")
            user_params_json = {}

        return user_params_json

    def _infer_brand_voice_from_brand_data(self, brand_config):
        prompt = generate_brand_analysis_prompt({
            'website_url':brand_config.get('website_url')
        })

        llm_response = self.client.call_llm("user-profile-agent", [prompt])

        try:
            clean_response = re.sub(r"^```(?:json)?|```$", "", llm_response, flags=re.MULTILINE).strip()
            brand_data = json.loads(clean_response)

        except Exception as e:
            print(f"Error fetching user params={e}")
            brand_data = {}

        return brand_data



    def process_message(self, message):
        api_instance = BrandFetchApi(message)
        brand_data = {}
        brand_data = api_instance.get_brand_data()
        #brand_data = {'name': 'SUGAR Cosmetics', 'logos': ['https://local-gaana.s3.amazonaws.com/assets/brand_kit_automation/b58fd58d-0d89-4b93-858c-4006375228a9/3f6e60ff-071d-471d-9905-5a643813bbfc.png', 'https://local-gaana.s3.amazonaws.com/assets/brand_kit_automation/b58fd58d-0d89-4b93-858c-4006375228a9/ead470a1-62db-4626-ba1d-0c980aef5123.jpeg'], 'colors': [{'name': 'dark', 'color': 'rgb(28,28,28)'}, {'name': 'light', 'color': 'rgb(227,203,174)'}, {'name': 'accent', 'color': 'rgb(150,84,124)'}], 'fonts': {'title': {'font': 'Karla', 'weight': '', 'size': 0}, 'subtitle': {'font': '', 'weight': '', 'size': 0}, 'body': {'font': 'var(--bs-body-font-family)', 'weight': '', 'size': 0}}}

        if brand_data.get('error_message'):
            error_message = f"Error Occured in Brand Fetch API for {message}.{brand_data.get('error_message')}"
            send_slack_message(error_message)
            
            return {'success':False, 'error_message': brand_data.get('error_message')}
        
        input_data = message.copy()

        research_data = self._infer_brand_voice_from_brand_data({
                'website_url': input_data.get('website_url')
            })

        if research_data:
            brand_data.update(research_data)

        else:
            error_message = f"Error occured in Brand Fetch LLM model query for GEMINI: {message}"
            send_slack_message(error_message)

            claude_instance = BrandKitAutomationClaudeView(input_data)
            research_data = claude_instance.generate_research_data()

            if research_data.get('info'):
                brand_data.update(research_data)
            else:
                error_message = f"Error occured in Brand Fetch LLM model query for claude: {message}"
                send_slack_message(error_message)

                return {'success':False, 'error_message': error_message}


        user_params = self._infer_human_parameters_from_brand_data({
            'brand_name': input_data.get('brand_name'),
            'brand_website': input_data.get('website_url'),
            'instagram_url': input_data.get('instagram_url')
        })

        brand_data['user_params'] = user_params
        
        output_format = self._create_response_format(brand_data)
        output_format['brand_id'] = input_data.get('brand_id')
        output_format['is_approved'] = False

        return {'success':True, 'output_format': output_format}




if __name__ == "__main__":
    x = BrandKitAutomater()
    
    input_data = {
        'brand_id':f"{uuid.uuid4()}",
        'website_url':"reebok.abfrl.in",
        'brand_name': "Reebok",
        'instagram_url':"https://www.instagram.com/reebokindia/"
        
    }

    instance = BrandKitAutomater()
    ans = instance.process_message(input_data)
    print(ans)
    send_slack_message("hello world")
