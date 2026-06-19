"""
Background Removal Service - Lambda Handler

This module contains the AWS Lambda handler for the background removal service.
It processes SQS messages containing S3 image paths and removes backgrounds using
the BackgroundRemover class.
"""

import json
import os
import logging
import traceback
import time

import boto3
import newrelic.agent

from typing import Dict, Any, Tuple, Optional

from bg_remover import BackgroundRemover
from common.custom_newrelic import CustomNewRelic

# Configure logging
newrelic.agent.initialize()
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


# Initialize AWS clients
s3 = boto3.client('s3')
sqs = boto3.client('sqs')

def setup_background_remover() -> BackgroundRemover:
    """
    Initialize the BackgroundRemover with proper error checking.

    Returns:
        BackgroundRemover: Configured background remover instance

    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        if not os.environ.get("FAL_KEY"):
            logger.error("FAL_KEY environment variable is required")
            raise ValueError("FAL_KEY environment variable is required")

        return BackgroundRemover()
    except Exception as e:
        logger.error(f"Failed to initialize BackgroundRemover: {str(e)}")
        raise

def parse_sqs_message(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse an SQS message and validate its contents.

    Args:
        record: SQS record from the Lambda event

    Returns:
        Dict containing the parsed message

    Raises:
        ValueError: If message is invalid or missing required fields
    """
    try:
        message = json.loads(record["body"])

        # Extract image URL from message
        # Check for various possible image keys in the message
        image_url = None

        # Direct image URL fields
        if "s3_link" in message:
            image_url = message["s3_link"]
        elif "image_key" in message:
            image_url = message["image_key"]
        elif "image_s3_key" in message:
            image_url = message["image_s3_key"]
        elif "image_url" in message:
            image_url = message["image_url"]

        # Check if we have a latest.json format message
        elif "content_pillar" in message and "posts" in message["content_pillar"]:
            # Extract the first post's image URL
            posts = message["content_pillar"]["posts"]
            if posts and "image_s3_key" in posts[0]:
                image_url = posts[0]["image_s3_key"]

        # Check if image_url was found
        if not image_url:
            raise ValueError("No image URL found in message. Required fields: s3_link, image_key, image_s3_key, or image_url")

        # Create a standardized message format
        standardized_message = {
            "s3_link": image_url,
            "output_key_prefix": message.get("output_key_prefix", "processed/"),
            "callback_queue_url": message.get("callback_queue_url", None)
        }

        message.update(standardized_message)

        logger.info(f"Parsed image URL: {image_url}")
        return message

    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in SQS message: {record['body']}")
    except Exception as e:
        raise ValueError(f"Error parsing message: {str(e)}")

def process_image(bg_remover: BackgroundRemover, message: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Process a single image using the background remover.

    Args:
        bg_remover: BackgroundRemover instance
        message: Parsed message with image information

    Returns:
        Tuple of (output_path, error_dict)
    """
    start_time = time.time()
    s3_link = message["s3_link"]

    logger.info(f"Processing image: {s3_link}")

    try:
        output_path, error_dict = bg_remover.remove_background(s3_link)

        process_time = time.time() - start_time
        logger.info(f"Successfully processed image in {process_time:.2f}s: {s3_link}")

        # Add response data if needed
        if message.get("response_queue"):
            # Here we could send a message to a response queue if needed
            pass

        return output_path, error_dict

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Failed to process image in {process_time:.2f}s: {s3_link}")
        logger.error(f"Error: {str(e)}")

        return None, {"error": str(e), "isvalid": False}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function for the background removal service.

    Args:
        event: Lambda event containing SQS records
        context: Lambda context

    Returns:
        Response dictionary with processing results
    """
    function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown_lambda")
    application = newrelic.agent.application()
    with newrelic.agent.BackgroundTask(application=application, name=function_name, group="lambda"):
        try:
            # Initialize the background remover
            bg_remover = setup_background_remover()

            results = []
            failed_count = 0

            # Process each record in the batch
            for index, record in enumerate(event.get("Records", [])):
                try:
                    message = parse_sqs_message(record)
                    CustomNewRelic.record_event("GeneratePostCreation", {
                        "generated_post_id": message.get("generated_post_id", "generated_post_id_not_available"),
                        "generate_config_id": message.get("generate_config_id", "generate_config_id_not_available"),
                        "brand_id": message.get("brand_id", "brand_id_not_available"),
                        "user_id": message.get("user_id", "user_id_not_available"),
                        "item_id": message.get("item_id", "item_id_not_available"),
                        "post_type": message.get("post_type", "post_type_not_available"),
                        "action": "background removal service received",
                        "error": ""
                    })

                    output_path, error_dict = process_image(bg_remover, message)
                    if output_path:
                        results.append({
                            "s3_link": message["s3_link"],
                            "output_path": output_path,
                            "success": True
                        })
                        CustomNewRelic.record_event("GeneratePostCreation", {
                            "s3_link": message["s3_link"],
                            "generated_post_id": message.get("generated_post_id", "generated_post_id_not_available"),
                            "generate_config_id": message.get("generate_config_id", "generate_config_id_not_available"),
                            "brand_id": message.get("brand_id", "brand_id_not_available"),
                            "user_id": message.get("user_id", "user_id_not_available"),
                            "item_id": message.get("item_id", "item_id_not_available"),
                            "post_type": message.get("post_type", "post_type_not_available"),
                            "action": "background removal service success",
                        })
                    else:
                        results.append({
                            "s3_link": message["s3_link"],
                            "error": error_dict,
                            "success": False
                        })
                        failed_count += 1
                        CustomNewRelic.record_event("GeneratePostCreation", {
                            "s3_link": message["s3_link"],
                            "generated_post_id": message.get("generated_post_id", "generated_post_id_not_available"),
                            "generate_config_id": message.get("generate_config_id", "generate_config_id_not_available"),
                            "brand_id": message.get("brand_id", "brand_id_not_available"),
                            "user_id": message.get("user_id", "user_id_not_available"),
                            "item_id": message.get("item_id", "item_id_not_available"),
                            "post_type": message.get("post_type", "post_type_not_available"),
                            "action": "background removal service failed",
                            "error": result[index].get("error", "error_not_available"),
                        })

                except ValueError as e:
                    logger.error(f"Invalid message: {str(e)}")
                    failed_count += 1
                    results.append({
                        "error": str(e),
                        "success": False
                    })
                    CustomNewRelic.record_event("GeneratePostCreation", {
                        "generated_post_id": message.get("generated_post_id", "generated_post_id_not_available"),
                        "generate_config_id": message.get("generate_config_id", "generate_config_id_not_available"),
                        "brand_id": message.get("brand_id", "brand_id_not_available"),
                        "user_id": message.get("user_id", "user_id_not_available"),
                        "item_id": message.get("item_id", "item_id_not_available"),
                        "post_type": message.get("post_type", "post_type_not_available"),
                        "action": "BG service value error",
                        "error": f"{e}"
                    })
                except Exception as e:
                    logger.error(f"Error processing record: {str(e)}")
                    logger.error(traceback.format_exc())
                    failed_count += 1
                    results.append({
                        "error": str(e),
                        "success": False
                    })
                    CustomNewRelic.record_event("GeneratePostCreation", {
                        "generated_post_id": message.get("generated_post_id", "generated_post_id_not_available"),
                        "generate_config_id": message.get("generate_config_id", "generate_config_id_not_available"),
                        "brand_id": message.get("brand_id", "brand_id_not_available"),
                        "user_id": message.get("user_id", "user_id_not_available"),
                        "item_id": message.get("item_id", "item_id_not_available"),
                        "post_type": message.get("post_type", "post_type_not_available"),
                        "action": "BG service exception error",
                        "error": f"{e}"
                    })

            # Return processing results
            CustomNewRelic.record_event("GeneratePostCreation", {
                "generated_post_id": message.get("generated_post_id", "generated_post_id_not_available"),
                "generate_config_id": message.get("generate_config_id", "generate_config_id_not_available"),
                "brand_id": message.get("brand_id", "brand_id_not_available"),
                "user_id": message.get("user_id", "user_id_not_available"),
                "item_id": message.get("item_id", "item_id_not_available"),
                "post_type": message.get("post_type", "post_type_not_available"),
                "action": "BG service complete",
            })
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "processed": len(results),
                    "failed": failed_count,
                    "results": results
                })
            }

        except Exception as e:
            # Handle initialization or other errors
            logger.error(f"Lambda execution failed: {str(e)}")
            logger.error(traceback.format_exc())

            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": str(e)
                })
            }

# For local testing
if __name__ == "__main__":
    # Local test event
    test_event = {
        "Records": [{
            "body": json.dumps({
                "s3_link": "./assets/printer.jpg"
                # Uncomment to test with S3
                # "s3_link": "s3://staging-gaana/assets/brands/02055e49-19f7-450b-b886-c9c51322b73d/social/instagram/e22cd8fb-efe8-4e0f-833b-14740ed6eedf/posts/04070f2d-719f-4b4a-a1b9-771377a6c165/2024-03-28/7098a252-5022-43f4-832d-9dfc8891d0b8.jpg"
            })
        }]
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
