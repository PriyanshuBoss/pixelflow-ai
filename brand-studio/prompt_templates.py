def generate_brand_analysis_prompt(input_data) -> str:
    prompt = f"""
Analyze the brand's digital presence using the following URL: {input_data.get('website_url')}. Examine the homepage, product pages, "About Us" section, and available marketing content. Extract and synthesize information to populate the following structured brand kit.

1. **Brand Purpose:** Summarize the brand's core mission or purpose as expressed in their messaging.
2. **Brand Voice:** Characterize the tone and style of the brand's communication (e.g., formal, friendly, authoritative).
3. **Brand Tone:** Identify the emotional tone conveyed by the brand. Strictly select data from this list [Authoritative, Witty / Humorous, Playful, Casual, Formal, Professional, Friendly, Inspirational, Conversational, Educational]
4. **Audience:** Define the target audience demographics and psychographics.
5. **Emotion:** Capture the key emotions the brand aims to evoke in its audience. Strictly select data from this list [Trusting, Curious, Surprised, Urgent / Motivational, Empathetic, Calm / Soothing, Excited / Enthusiastic, Nostalgic, Confident, Joyful]
6. **Character:** Describe the brand personality traits. Strictly select data from this list [Persistent, Compassionate, Sophisticated, Adventurous, Reliable / Trustworthy, Quirky, Energetic, Innovative, Bold, Down‑to‑Earth]
7. **Language:** Detect the primary language(s) used in brand messaging. Strictly select data from this list [Informal / Colloquial, Simple / Clear, Inclusive / Person‑centric, Direct / Concise, Technical / Jargon‑heavy, Poetic / Descriptive, Authority‑Driven, Storytelling‑focused, Formal, Elaborate / Rich]

Output Format (JSON): STRICTLY return the data in valid json format
{{
  "brand_voice": {{
    "purpose": "[Summarized brand mission or purpose]",
    "audience": "[Target demographics and psychographics]",
    "tone": [
      "[tone-style-1]",
      "[tone-style-2]",
      "[tone-style-3]"
    ],
    "emotion": [
      "[emotion-1]",
      "[emotion-2]",
      "[emotion-3]"
    ],
    "character": [
      "[personality-trait-1]",
      "[personality-trait-2]", 
      "[personality-trait-3]"
    ],
    "language": [
      "[primary language or communication style]"
    ]
  }}
}}

Consider data from website design, product copy, blog posts, banners, and any linked social media or videos. Use best-effort to infer missing details, maintaining consistency and logic with the brand’s apparent identity.

IMPORTANT: Do not return any other information apart from JSON specified.
"""
    return prompt.strip()


def generate_user_params_prompt_using_brand_configuration(brand_config):

    brand_name = brand_config.get('brand_name')
    brand_website = brand_config.get('brand_website')
    instagram_url = brand_config.get('instagram_url')

    prompt = f"""
    You are an expert market analyst.

    Input:
    - Brand Name: {brand_name}
    - Brand Website: {brand_website}
    - Instagram Url: {instagram_url}

    Task:
    Analyze the brand and its Instagram account to generate a target audience profile. Focus only on ethnicity, age_group, gender, and region.

    Output:
    Return the result in the following JSON format:

    {{
        "ethnicity": ["Primary ethnic group(s) of the audience. Define country if possible"],
        "age_group": ["Approximate age range of the people who use the product"],
        "gender": ["Gender of the primary users (male, female, or mixed if equally likely)"],
        "region": ["Single specific geographic location (city or country) where the majority of users reside"]
    }}

    Guidelines:
    - Infer audience demographics from Instagram followers, engagement, and brand content.
    - Provide a single representative gender if dominant, otherwise use "mixed" for equally likely male/female users.
    - If the product is for children, indicate the age range of the children using it.
    - If the product is for adults, indicate the age range of adult users.
    - If exact information is unavailable, make the best-guess based on the brand’s products and content.
    - Keep JSON valid and clean.

    """
    
    return prompt
