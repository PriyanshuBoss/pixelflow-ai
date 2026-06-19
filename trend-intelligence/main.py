from claude import TrendInsightsClaudeView
from db import save_trends_to_dynamodb
from perplexity import TrendsInsightsPerplexityView
class TrendsProcessor:
    """
    A consumer class that reads messages from an SQS queue and processes them
    for trend insights generation.
    """

    def __init__(self):
        """Initialize the SQS consumer with queue configuration."""
        pass


    def _get_trends_using_claude(self, input_data):
        claude_trends = TrendInsightsClaudeView(input_data)
        research_data = claude_trends.generate_research_data()
        
        return research_data
        

    def _get_trends_using_perplexity(self, input_data):
        perplexity_trends = TrendsInsightsPerplexityView(input_data)
        research_data = perplexity_trends.generate_research_data()

        return research_data
        

        

    def process_message(self, message):
        """Process a message for trend insights generation."""
        try:
            # Validate required fields
            required_fields = ['brand_id','start_date', 'end_date', 'website_url','created_at']
            missing_fields = [field for field in required_fields if field not in message]
            
            if missing_fields:
                return {
                    'success': False, 
                    'error_message': f"Missing required fields: {missing_fields}"
                }

            print(f"Processing trends for brand: {message.get('website_url')}")

            
            input_data = {}
            input_data.update(message)

            if message.get('prompt'):
                input_data['prompt'] = message['prompt']

            if message.get('ai_llm'):
                input_data['ai_llm'] = message['ai_llm'].lower()
            else:
                input_data['ai_llm'] = 'perplexity'

            if input_data['ai_llm'] == 'claude':
                research_data = self._get_trends_using_claude(input_data)
            else:
                research_data = self._get_trends_using_perplexity(input_data)

            save_trends_to_dynamodb(input_data, research_data)
            
            
            return {'success': True}

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return {'error_message': str(e), 'success': False}


if __name__ == "__main__":
    
    # input_data = {
    #     "start_date": 1717286400,
    #     "end_date": 1719878400,
    #     "website_url": "https://onlyvimal.co.in/",
    #     "brand_id": "f0c5757a-ef2a-4700-ad13-c446bba7b5c5",
    #     "ai_llm":"perplexity",
    #     "ai_model":"llama-3.1-sonar-large-128k-online"
        
    # }

    input_data = {
        "start_date": 1717286400,
        "end_date": 1719878400,
        "website_url": "https://onlyvimal.co.in/",
        "brand_id": "f0c5757a-ef2a-4700-ad13-c446bba7b5c5",
        "ai_llm":"claude",
        "ai_model":"claude-3-5-sonnet-latest"
        
    }
    
    claude_trends = TrendInsightsClaudeView(input_data)
    research_data = claude_trends.generate_research_data()

    # perplexity_trends = TrendsInsightsPerplexityView(input_data)
    # research_data = perplexity_trends.generate_research_data()
    # save_trends_to_dynamodb(input_data, research_data)
