import os
import boto3
import uuid
import time
from botocore.exceptions import ClientError

def save_trends_to_dynamodb(input, data):
    """
    Save structured brand insight data to DynamoDB.
    
    Args:
        data (dict): The JSON object containing brand insights.
        table_name (str): Name of the DynamoDB table.
        
    Returns:
        str: Message indicating success or failure.
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = os.getenv('TRENDS_TABLE_NAME')
    table = dynamodb.Table(table_name)
    created_at = input.get('created_at', int(time.time()))

    print("info passed")
    print(data.get('info',[]))

    try:
        brand_id = input.get("brand_id", str(uuid.uuid4()))
        item = {
            "brand_id": brand_id,
            "website_url": input.get("website_url", ""),
            'ai_llm': input.get('ai_llm'),
            "start_date": input.get("start_date"),
            "end_date": input.get("end_date"),
            "created_at": created_at,
            "info": data.get('info'),
            "prompt": data.get('prompt'),
            'ai_model': data.get('ai_model')
        }
        # Save item to DynamoDB
        table.put_item(Item=item)
        print(f"Data for brand_id {brand_id} successfully saved to {table_name}.")
        

    except ClientError as e:
        print(f"Failed to save data: {e.response['Error']['Message']}")
