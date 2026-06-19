import os


from openai import AzureOpenAI

class CustomOpenAIClient:

    def __init__(self):
        OPENAI_API_URL ="https://customopenaiinstance.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"

        self.client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_KEY'),
            api_version="2024-05-01-preview",
            azure_endpoint=OPENAI_API_URL
        )

    def call_open_ai(self, payload):
        content = []

        asset_base64_list = payload.get('asset_base64_list', [])
        prompt_text = payload.get('prompt_text')
        module = payload.get('module')


        for asset_base64 in asset_base64_list:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{asset_base64}",
                    "detail": "auto"
                }
            })

        if prompt_text:
            content.append({"type": "text", "text": prompt_text})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"[ERROR] OpenAI API call failed for {module}: {e}")
            return ""
