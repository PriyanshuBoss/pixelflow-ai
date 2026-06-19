#!/usr/bin/env python
import random


class AgentConfig:
    def __init__(self):
        self.config = {
            "set_base": {
                "current": (
                    "Take a look at this image and understand this product. "
                    "I want to generate a scene with this product present in it. "
                    "Pay extra attention to the details, textures, colors, proportions, text, "
                    "and overall appearance. Never alter them and preserve them as is. "
                    "The user prompt you will be provided next takes priority. "
                    "Please confirm you are ready for image generation instructions."
                ),
                "experimental": (
                    "I want to edit this image. Please confirm you can see it and are ready "
                    "for editing instructions. Pay extra attention to the details, textures, colors, "
                    "proportions, text, and overall appearance. Never alter them and preserve them as is."
                ),
                "furnishka": (
                    "Take a look at this image and understand this product. "
                    "I want to generate a scene with this product present in it. "
                    "Pay extra attention to the details, textures, colors, proportions, text, "
                    "and overall appearance. Never alter them and preserve them as is. "
                    "The user prompt you will be provided next takes priority."
                ),
            },
            "background_generator": {
                "current": (
                    "Generate photorealistic scene prompt with precise product placement, reconstruction, part emphasis. "
                    "Leverage natural language for seamless background integration.\n"
                    "## Product Analysis Protocol\n"
                    "- Material textures (matte, glossy, fabric, metal)\n"
                    "- Brand elements (logos, text, labels) - preserve exactly\n"
                    "- Proportions and viewing angle\n"
                    "- Color palette and lighting characteristics\n"
                    "## Scene Construction Methodology\n"
                    "- Use professional photography terminology\n"
                    "- Specify lens and lighting details\n"
                    "- Transform placement requests into photographic directions\n"
                    "- Preserve all brand elements and text exactly\n"
                    "## Critical requirements\n"
                    "- Never alter product details\n"
                    "- User description is main driver\n"
                    "## Output\n"
                    "Single coherent paragraph, <256 characters, professional photography language, natural integration."
                ),
                "furnishka": "Same as 'current', specific for Furnishka use.",
                "experimental": "More advanced/experimental version with similar structure but optimized for Nano Banana workflow.",
                "current-v1": (
                    "Generate photorealistic scene prompt with precise product placement, reconstruction, part emphasis. "
                    "Leverage natural language for seamless background integration.\n"
                    "## Product Analysis Protocol\n"
                    "- Material textures (matte, glossy, fabric, metal)\n"
                    "- Brand elements (logos, text, labels) - preserve exactly\n"
                    "- Proportions and viewing angle\n"
                    "- Color palette and lighting characteristics\n"
                    "## Scene Construction Methodology\n"
                    "- Use professional photography terminology\n"
                    "- Specify lens and lighting details\n"
                    "- Transform placement requests into photographic directions\n"
                    "- Preserve all brand elements and text exactly\n"
                    "{user_params}\n"
                    "{brand_voice}\n"
                    "## Critical requirements\n"
                    "- Never alter product details\n"
                    "- User description is main driver\n"
                    "## Output\n"
                    "Single coherent paragraph (<256 characters) written strictly in the brand's tone, emotion, and language."
                    "Use professional photography language with natural integration. No deviation from brand voice permitted."
                ),
                "current-v1-multi-products": (
                    "Generate photorealistic scene prompt with precise product placement, reconstruction, part emphasis. "
                    "Leverage natural language for seamless background integration.\n"
                    "## Product Analysis Protocol\n"
                    "- Material textures (matte, glossy, fabric, metal)\n"
                    "- Brand elements (logos, text, labels) - preserve exactly\n"
                    "- Proportions and viewing angle\n"
                    "- Color palette and lighting characteristics\n"
                    "## Scene Construction Methodology\n"
                    "- Use professional photography terminology\n"
                    "- Specify lens and lighting details\n"
                    "- Transform placement requests into photographic directions\n"
                    "- Preserve all brand elements and text exactly\n"
                    "## Multiple products\n"
                    "- Make sure to create a prompt which will use all of the provided product images in the final scene.\n"
                    "{user_params}\n"
                    "{brand_voice}\n"
                    "## Critical requirements\n"
                    "- Never alter product details\n"
                    "- User description is main driver\n"
                    "## Output\n"
                    "Single coherent paragraph (<512 characters) written strictly in the brand's tone, emotion, and language."
                    "Use professional photography language with natural integration. No deviation from brand voice permitted."
                ),
            },
            "brand_compliance_reviewer": {
                "current": "Score final image against original asset and user intent using defined metrics. Output JSON only.",
                "experimental": "Advanced evaluation using natural language assessment, optimized for Nano Banana. Output JSON only.",
            },
            "image_editing_expert": {
                "current": "Compare original product asset with generated image. Focus on asset preservation and background accuracy. Output JSON only."
            },
            "fashion_generator": {
                "current": (
                    "Analyze clothing asset and user description. Generate model wearing clothing in scene. "
                    "Output <256 chars.\n"
                    "## Input Parsing\n"
                    "- Extract age, gender, activity, context, view\n"
                    "- Analyze clothing type, key features, material, fit\n"
                    "## Model Generation Rules\n"
                    "- Age → model proportions\n"
                    "- Activity → pose\n"
                    "- View → camera alignment\n"
                    "## Output Structure\n"
                    "Generate [age] year old [gender] wearing [clothing], [activity/pose], in [scene/location]."
                ),
                "current-v1": (
                    "Analyze clothing asset and user description. Generate model wearing clothing in scene. "
                    "Output <256 chars.\n"
                    "## Input Parsing\n"
                    "- Extract age, gender, activity, context, view\n"
                    "- Analyze clothing type, key features, material, fit\n"
                    "{user_params}\n"
                    "{brand_voice}\n"
                    "## Model Generation Rules\n"
                    "- Age → model proportions\n"
                    "- Activity → pose\n"
                    "- View → camera alignment\n"
                    "## Output Structure\n"
                    "Generate [age] year old [gender] of [ethnicity], wearing [clothing], [activity/pose], in [scene/location] matching region context."
                ),
                "current-v1-multi-products": (
                    "Analyze clothing assets and user description. Generate multiple models appropriate for the asset, wearing the given clothing in the scene. "
                    "Output <512 chars.\n"
                    "## Input Parsing\n"
                    "- Extract age, gender, activity, context, view\n"
                    "- Analyze clothing type, key features, material, fit\n"
                    "{user_params}\n"
                    "{brand_voice}\n"
                    "## Model Generation Rules\n"
                    "- Age → model proportions\n"
                    "- Activity → pose\n"
                    "- View → camera alignment\n"
                    "## Multiple products\n"
                    "- Make sure to create a prompt which will use all of the proveded assets in the final image.\n"
                    "## Output Structure\n"
                    "Generate [age] year old [gender] of [ethnicity], wearing [clothing], [activity/pose], in [scene/location] matching region context."
                ),
            },
            "fashion_editing_expert": {
                "current": (
                    "Compare original clothing asset with generated fashion model image. "
                    "Assess clothing accuracy, model quality, and scene match. Output JSON only."
                )
            },
            "image_title_caption_generator": {
                "current": (
                    "Analyze the given scene and generate an appropriate post title and caption.\n"
                    "## Output Schema\n"
                    "```json\n"
                    "{\n"
                    '  "post_title": "50 chars max",\n'
                    '  "post_caption": "100 chars max"\n'
                    "}\n"
                    "```\n"
                    "ONLY RETURN VALID JSON AND NOTHING ELSE"
                )
            },
        }

    def get(self, agent_name: str) -> dict:
        agent_config = self.config.get(agent_name)

        if not agent_config:
            raise Exception(f"Agent '{agent_name}' not found in configuration")

        return agent_config


def generate_human_parameters_section(user_params):

    def pick_random(value):
        if isinstance(value, list) and value:
            return random.choice(value)
        elif isinstance(value, str):
            return value
        return ""

    ethnicity = user_params.get("ethnicity")
    age_group = user_params.get("age_group")
    gender = user_params.get("gender")
    region = user_params.get("region")

    ethnicity = pick_random(ethnicity)
    age_group = pick_random(age_group)
    gender = pick_random(gender)
    region = pick_random(region)

    scene_lines = []

    if ethnicity:
        scene_lines.append(f"- Ethnicity: {ethnicity}")
    if age_group:
        scene_lines.append(f"- Age group: {age_group}")
    if gender:
        scene_lines.append(f"- Gender: {gender}")
    if region:
        scene_lines.append(f"- Region / Location context: {region}")

    if scene_lines:

        scene_guidelines = (
            "## Scene Guidelines\n" + "\n".join(scene_lines) + "\n\n"
            "## Human Model Inclusion Protocol\n"
            "- Include realistic human models when relevant to the scene\n"
            "- Match model appearance to ethnicity, age_group, and gender provided\n"
            "- Ensure natural interaction with the product (e.g., wearing, using, holding)\n"
            "- If multiple genders are provided, depict either a single representative model or a combination "
            "(e.g., couple, male and female) depending on scene context\n"
            "- Use professional pose and expression suited to commercial photography\n"
            "- Maintain focus on the product while ensuring human integration looks organic\n"
        )

        return scene_guidelines

    return ""


def generate_brand_voice_section(brand_voice: dict) -> str:
    """
    Takes a brand_voice dictionary and returns a formatted string
    ready to be inserted into a prompt. Lists are joined with commas.
    """

    def join_list(key):
        return ", ".join(brand_voice.get(key, []))

    return (
        "## Brand Voice\n"
        f"Purpose: {brand_voice.get('purpose', '')}.\n"
        f"Audience: {brand_voice.get('audience', '')}.\n"
        f"Tone: {join_list('tone')}.\n"
        f"Emotion: {join_list('emotion')}.\n"
        f"Character: {join_list('character')}.\n"
        f"Language: {join_list('language')}.\n"
        "### Enforcement Directives\n"
        "- All descriptive language, phrasing, and emotional undertones must align strictly "
        "with the specified brand tone, emotion, and character.\n"
        "- The output’s style, rhythm, and linguistic choices must reflect the brand’s language style exactly.\n"
        "- Maintain full product integrity — no alterations to design, text, or proportions.\n"
        "- Brand voice governs expressive framing, mood, and word choice absolutely.\n"
        "- Any default or generic style must be overridden by the brand voice profile."
    )


def generate_human_check_prompt(system_description, user_given_description):

    if not user_given_description:
        user_given_section = ""
    else:
        user_given_section = f"User Given Description:\n {user_given_description}"
    
    prompt = f"""
        Read the following combined scene descriptions carefully:

        Base Description:
        "{system_description}"

        "{user_given_section}"

        Based on the visual and contextual details, tell me only "Yes" or "No" — 
        does this scene require a human presence on camera (in the visuals)?
        Do not explain your reasoning, just output "Yes" or "No".
        """
    return prompt.strip()
