import json

from .custom_openai_client import CustomOpenAIClient


class ImageAnalyser:

    def __init__(self, asset_base64_list):
        self.asset_base64_list = asset_base64_list
        self.openai_client = CustomOpenAIClient()

    def _create_prompt_for_image_analysis(self):
        prompt = """
# Product Comparison Instructions

Compare the two images (and optional text if provided). Return only JSON in the following structure:

- **similarity**: a detailed description of what looks alike between the products
- **differences**: a detailed description of what is different between the products
- **scores**: include sub-scores from 0–10 for:
  - color
  - material
  - design_style
  - product_type
  - text_similarity (If no text is provided, set text_similarity to null and text_used to false. If text is provided, compute a numeric score and set text_used to true)
- **final_score**: calculate a weighted similarity score with weightage from 0–10, renormalizing weights if any category is excluded

## Weightage Guide

- **design_style**: 30%
- **product_type**: 30%
- **material**: 15%
- **color**: 25%

## Comparison Guidelines

Be very strict in comparison: if there are any visible differences in structure, features, proportions, or design (such as storage drawers, legs vs. no legs, handles, finishes, or frame type), treat them as different products.

- Lower design_style and product_type scores significantly if the structure differs
- The `final_score` should reflect whether a buyer would realistically think they are the exact same product, not just similar in style or material
- Full product visibility is mandatory. If either image is cropped, cut off, or obscured so that the entire product structure cannot be confirmed:
  - Note this explicitly in similarity and differences and calculation of final score.
  - Assign low design_style, product_type, and final_score values to reflect uncertainty (do not exceed 5)..

## Output Format

Only output valid JSON. Do not include any explanation outside the JSON.
"""
        return prompt.strip()

    def analyse_image_similarity(self):
        prompt = self._create_prompt_for_image_analysis()
        response = self.openai_client.call_open_ai({
            'prompt_text':prompt,
            'asset_base64_list': self.asset_base64_list,
            'module':"Image Analysis"
        })

        data = {}

        try:
            data = json.loads(response)
        except Exception as e:
            print(f"Image Analysis Failed-{e}")

        return data
