#!/usr/bin/env python3
import random
import math


class AgentConfig:
    def __init__(self):
        self.config = {
            "prompt_library": {
                "single_asset": (
                    "Look at the images provided to you. All of the input images are of a single asset at different angles. "
                    "Understand the product thoroughly and generate a free flowing prompt which will be used to create an image for this product. "
                    "Follow these principles: Generate photorealistic scene prompt with precise product placement, reconstruction, part emphasis. "
                    "Leverage natural language for seamless background integration.\n"
                    "## Product Analysis Protocol\n"
                    "Extract visual elements:\n"
                    "- Material textures (matte, glossy, fabric, metal)\n"
                    "- Brand elements (logos, text, labels) - preserve exactly\n"
                    "- Proportions and viewing angle. Understand the original scale/perspective. You will need to adjust to users request.\n"
                    "- Color palette and lighting characteristics\n"
                    "## Scene Construction Methodology\n"
                    "### Photography Language Integration\n"
                    "- Use professional terminology: 'captured with', 'illuminated by', 'shot from'\n"
                    "- Specify lens characteristics when relevant: 'wide-angle perspective', 'portrait lens compression'\n"
                    "- Include lighting conditions: 'soft natural lighting', 'dramatic side lighting', you can describe how the lighting is adjusted for the perfect product shot.\n"
                    "### Positioning Strategy\n"
                    "Transform placement requests into photographic directions:\n"
                    "- 'left/right' -> 'positioned in the [left/right] third of the frame'\n"
                    "- 'foreground/background' -> 'prominently featured in foreground' / 'artfully placed in background'\n"
                    "- 'on [surface]' -> 'naturally resting on [surface] with realistic shadows'\n"
                    "### Natural Language Preservation\n"
                    "Critical preservation commands:\n"
                    "- 'Keep all text and logos exactly as shown in the original'\n"
                    "- 'Preserve every detail of the brand elements'\n"
                    "## Critical requirements\n"
                    "- Never alter the product details and always preserve them as is.\n"
                    "- Make sure to give heavy emphasis to what the user wants to see in the final image. "
                    "Your task is to coherently place the product, and background elements, in a believable scene. "
                    "The user's description should be the main driving force behind your prompt.\n"
                    "## Output Template\n"
                    "```\n"
                    "A photorealistic scene of [product description with key details] [positioned naturally/placed strategically] "
                    "[in/on/near specified location]. The scene features [background elements from user prompt], "
                    "captured with [appropriate camera language]. [Lighting description that complements both product and scene]. "
                    "All original text, logos, and proportions preserved exactly as shown.\n"
                    "You are not required to follow this exact format but make sure to keep your prompts under 512 characters.\n"
                    "```\n"
                    "## Optimization Rules\n"
                    "- Narrative flow over keyword lists\n"
                    "- Single coherent scene description\n"
                    "- Professional photography language\n"
                    "- Natural integration terminology\n"
                    "- <512 characters total\n"
                    "## Output Format\n"
                    "Single flowing paragraph. No quotes."
                ),
                "direct_single_image_generation": (
                    "Generate an image with this prompt and do not change the input image while generating the output"
                ),
                "script_generator_1": (
                    "Generate a script which will be used in a visual product video showcase. "
                    "The video will be {duration} seconds long. Use the users idea as a starting point. "
                    "Look at the provided image and think of how it can work with the user idea. "
                    "Only provide the script and nothing else. Make sure the screenplay is long enough to meet the duration requirements."
                ),
                "script_generator_2": (
                    "Generate a script which will be used in a visual product video showcase. "
                    "The video will be {duration} seconds long. Use the users idea as a starting point. "
                    "Look at the provided image and think of how it can work with the user idea. Only provide the script and nothing else. "
                    "Follow the example output format below.\n"
                    "## Script Title\n\n"
                    "**Video Length:** 20 seconds\n\n"
                    "**Scene:** A pristine, bustling professional kitchen. Sunlight streams through a large window.\n\n"
                    "**(0-4 seconds)**\n\n"
                    "**VISUAL:** Close-up shot of a chef's hands, deftly chopping fresh herbs on a wooden cutting board. "
                    "The movements are precise and confident.\n\n"
                    "**AUDIO:** The rhythmic, satisfying sound of a knife chopping. Light, sophisticated background music begins.\n\n"
                    "**(4-8 seconds)**\n\n"
                    "**VISUAL:** The chef, a distinguished-looking individual in a crisp white chef's coat, smiles subtly as he looks at the ingredients. "
                    "He reaches for a jar of Hellmann's Real Mayonnaise. The jar is prominently displayed on a clean stainless steel counter, catching the light.\n\n"
                    "**AUDIO:** Music swells slightly, a hint of anticipation.\n\n"
                    "**(8-12 seconds)**\n\n"
                    "**VISUAL:** The chef expertly opens the Hellmann's jar. He scoops out a perfect dollop of the creamy, white mayonnaise with a spoon and adds it to a mixing bowl filled with other fresh ingredients. "
                    "He then begins to gently fold the ingredients together.\n\n"
                    "**AUDIO:** Soft, gentle mixing sounds. Music remains elegant and understated.\n\n"
                    "**(12-18 seconds)**\n\n"
                    "**VISUAL:** A quick montage of appetizing dishes being prepared, each subtly showcasing the versatility of Hellmann's. "
                    "Perhaps a perfectly seared piece of fish with a delicate aioli, or a beautifully plated gourmet burger. "
                    "The Hellmann's jar is visible in the background of one shot.\n\n"
                    "**AUDIO:** Music becomes a bit more dynamic, reflecting the energy of creation.\n\n"
                    "**(18-22 seconds)**\n\n"
                    "**VISUAL:** A final hero shot: the Hellmann's Real Mayonnaise jar, perfectly centered, with a soft focus on the label. "
                    "A subtle glow emanates from behind it.\n\n"
                    "**AUDIO:** Music reaches a gentle crescendo and then fades out. "
                    "A confident, warm voiceover states:\n\n"
                    "**VOICEOVER:** 'Hellmann's. The mark of a true chef.'"
                ),
                "script_analyzer_1": (
                    "Analyze the current image and script. Your objective is to create keyframe image prompts which will be used to generate a video. "
                    "We will create N number of keyframe images each of varying seconds adding up to {duration} seconds. "
                    "Your output format is as follows. Make sure to use the input image in the compositions."
                ),
                "script_analyzer_2": (
                    "Analyze the current image and script. Your objective is to create keyframe image prompts which will be used to generate a video. "
                    "We will create N number of images which we will use as keyframes for a video of lengths 4, 6, and 8 seconds only, adding up to {duration} seconds. "
                    "You can round up to the next smallest number. Make sure to use the input image in the composition. "
                    "Each keyframe must represent a visual segment with a duration strictly between 4 and 8 seconds — no shorter or longer. "
                    "Your output format is as follows."
                ),
                "script_generator_4": (
                    "Generate a script which will be used in a visual product video showcase. "
                    "The video will be {duration} seconds long. Use the users idea as a starting point. "
                    "Look at the provided image and think of how it can work with the user idea. "
                    "Only provide the script and nothing else. Follow the example output format below. "
                    "Add more segments to reach the target total duration.\n"
                    "## Script Title\n\n"
                    "**Video Length:** 20 seconds\n\n"
                    "**Scene:** Detailed description of the scene\n\n"
                    "**(0-4 seconds)**\n\n"
                    "**VISUAL:** Description of the action in detail.\n\n"
                    "**AUDIO:** Audio that goes well with the scene."
                ),
                "script_analyzer_4": (
                    "Analyze the current image and script. Your objective is to create keyframe image prompts which will be used to generate a video. "
                    "We will create N number of images which we will use as keyframes for a video of lengths 4, 6, and 8 seconds only, adding up to {duration} seconds. "
                    "You can round up to the next smallest number. Make sure the input image is present in each keyframe unless it is b-roll. "
                    "If the keyframe is a b-roll, then the video segment prompt must not contain any elements of the product in it. "
                    "Make sure the first segment has a solid hook to grab attention and the ending segment concludes the narrative correctly. "
                    "Your output format is as follows."
                ),
                "script_generator_5": (
                    "Generate a script(text only) which will be used in a visual product video showcase having background music, no dialouges, no narration and no text overlays."
                    "The video will be {duration} seconds long. Use the users idea as a starting point. "
                    "Look at the provided image and think of how it can work with the user idea. "
                    "Only provide the script and nothing else. Follow the example output format below. "
                    "Add more segments to reach the target total duration.\n"
                    "Before writing, study and apply the following sections carefully. "
                    "These define how the brand communicates and how human subjects should appear in the scene:\n\n"
                    "{brand_voice}\n"
                    "{user_params}\n"
                    "Ensure that every scene, dialogue, and visual tone fully reflect the brand’s voice and match the demographic context provided.\n\n"
                    "Follow the example output format below.\n"
                    "## Script Title\n\n"
                    "**Video Length:** 20 seconds\n\n"
                    "**Scene:** A pristine, bustling professional kitchen. Sunlight streams through a large window.\n\n"
                    "**(0-4 seconds)**\n\n"
                    "**VISUAL:** Close-up shot of a chef's hands, deftly chopping fresh herbs on a wooden cutting board. "
                    "The movements are precise and confident. The scene captures the texture of the herbs, the motion of the knife, "
                    "and the gleam of natural morning light on the surface.\n\n"
                    "**(4-8 seconds)**\n\n"
                    "**VISUAL:** The chef, a distinguished individual in a crisp white chef's coat, smiles subtly as they look at the ingredients. "
                    "They reach for a jar of Hellmann's Real Mayonnaise. The jar is prominently displayed on a clean stainless steel counter, "
                    "reflecting soft daylight.\n\n"
                    "**(8-12 seconds)**\n\n"
                    "**VISUAL:** The chef expertly opens the Hellmann's jar. A smooth dollop of creamy mayonnaise is added to a mixing bowl filled "
                    "with vibrant, fresh ingredients. The camera captures the rich texture and glossy surface of the product in perfect detail.\n\n"
                    "**(12-18 seconds)**\n\n"
                    "**VISUAL:** A seamless montage of appetizing dishes being prepared, each subtly highlighting the versatility of Hellmann's. "
                    "A perfectly seared piece of fish with a delicate aioli, a beautifully plated gourmet burger, and a fresh salad being dressed. "
                    "The Hellmann's jar remains subtly visible in the background of one shot.\n\n"
                    "**(18-22 seconds)**\n\n"
                    "**VISUAL:** Final hero shot: the Hellmann's Real Mayonnaise jar, perfectly centered and illuminated by soft, diffused light. "
                    "The brand label is crisp and legible, with a warm glow around the jar. The scene concludes with a gentle visual fade, leaving "
                    "the product as the focal point."
                ),
                "script_analyzer_5": (
                    "Analyze the current image and script. Your objective is to create keyframe image prompts which will be used to generate a video. "
                    "We will create N number of images which we will use as keyframes for a video of lengths 4, 6, and 8 seconds only, adding up to {duration} seconds. "
                    "You can round up to the next smallest number. Make sure the input image is present in each keyframe unless it is b-roll. "
                    "If the keyframe is a b-roll, then the video segment prompt must not contain any elements of the product in it. "
                    "Make sure the first segment has a solid hook to grab attention and the ending segment concludes the narrative correctly.\n\n"
                    "### Brand Visual Alignment\n"
                    "{brand_voice}\n\n"
                    "### Demographic Visual Context\n"
                    "{user_params}\n\n"
                    "Your task: Generate coherent, photorealistic keyframe scene prompts that visually match the script tone, "
                    "brand personality, and demographic characteristics provided. "
                    "Each keyframe prompt should reflect brand emotion, lighting mood, and authenticity. "
                    "Only describe what is seen visually — no non-visual elements.\n\n"
                ),
                "script_generator_6": (
                    "Generate a script(text only) which will be used in a visual product video showcase having background music, no dialouges, no narration and no text overlays."
                    "The video will be {duration} seconds long. Use the users idea as a starting point. Each segment should be 8 seconds long."
                    "Look at the provided image and think of how it can work with the user idea. "
                    "Only provide the script and nothing else. Follow the example output format below. "
                    "Add more segments to reach the target total duration.\n"
                    "Before writing, study and apply the following sections carefully. "
                    "These define how the brand communicates and how human subjects should appear in the scene:\n\n"
                    "{brand_voice}\n"
                    "{user_params}\n"
                    "Ensure that every scene and visual tone fully reflect the brand’s voice and match the demographic context provided.\n\n"
                    "Follow the example output format below.\n"
                    "## Script Title\n\n"
                    "**Video Length:** 40 seconds\n\n"
                    "**Scene:** A pristine, bustling professional kitchen. Sunlight streams through a large window.\n\n"
                    "**(0-8 seconds)**\n\n"
                    "**VISUAL:** Close-up shot of a chef's hands, deftly chopping fresh herbs on a wooden cutting board. "
                    "The movements are precise and confident. The scene captures the texture of the herbs, the motion of the knife, "
                    "and the gleam of natural morning light on the surface.\n\n"
                    "**(8-16 seconds)**\n\n"
                    "**VISUAL:** The chef, a distinguished individual in a crisp white chef's coat, smiles subtly as they look at the ingredients. "
                    "They reach for a jar of Hellmann's Real Mayonnaise. The jar is prominently displayed on a clean stainless steel counter, "
                    "reflecting soft daylight.\n\n"
                    "**(16-24 seconds)**\n\n"
                    "**VISUAL:** The chef expertly opens the Hellmann's jar. A smooth dollop of creamy mayonnaise is added to a mixing bowl filled "
                    "with vibrant, fresh ingredients. The camera captures the rich texture and glossy surface of the product in perfect detail.\n\n"
                    "**(24-32 seconds)**\n\n"
                    "**VISUAL:** A seamless montage of appetizing dishes being prepared, each subtly highlighting the versatility of Hellmann's. "
                    "A perfectly seared piece of fish with a delicate aioli, a beautifully plated gourmet burger, and a fresh salad being dressed. "
                    "The Hellmann's jar remains subtly visible in the background of one shot.\n\n"
                    "**(32-40 seconds)**\n\n"
                    "**VISUAL:** Final hero shot: the Hellmann's Real Mayonnaise jar, perfectly centered and illuminated by soft, diffused light. "
                    "The brand label is crisp and legible, with a warm glow around the jar. The scene concludes with a gentle visual fade, leaving "
                    "the product as the focal point."
                ),
                "script_analyzer_6": (
                    "Analyze the current image and script. Your objective is to create keyframe image prompts which will be used to generate a video. "
                    "We will create N number of images which we will use as keyframes for a video of lengths 8 seconds only, adding up to {duration} seconds. "
                    "If the total duration cannot be matched perfectly, adjust the number of segments rather than changing their durations."
                    "You can round up to the next smallest number. Make sure the input image is present in each keyframe unless it is b-roll. "
                    "If the keyframe is a b-roll, then the video segment prompt must not contain any elements of the product in it. "
                    "Make sure the first segment has a solid hook to grab attention and the ending segment concludes the narrative correctly.\n\n"
                    
                    "### Brand Visual Alignment\n"
                    "{brand_voice}\n\n"
                    "### Demographic Visual Context\n"
                    "{user_params}\n\n"
                    
                    "Your task: Generate coherent, photorealistic keyframe scene prompts that visually match the script tone, "
                    "brand personality, and demographic characteristics provided. "
                    "Each keyframe prompt should reflect brand emotion, lighting mood, and authenticity. "
                    "Only describe what is seen visually — no non-visual elements.\n\n"
                ),

                "script_generator_7": (
                    "Generate a script (text only) which will be used in a visual product video showcase with background music, "
                    "no dialogues, no narration, and no text overlays. The video will be {duration} seconds long. Use the user's idea "
                    "as a starting point. Each segment should be 8 seconds long. Look at the provided image and think about how it can "
                    "work with the user's idea. Only provide the script and nothing else. Follow the example output format below. "
                    "Add more segments to reach the total duration.\n\n"

                    "Before writing, study and apply the following sections carefully. These define how the brand communicates and how "
                    "human subjects (if any) should appear in the scene:\n\n"
                    "{brand_voice}\n"
                    "{user_params}\n\n"
                    "Ensure that every scene, visual choice, emotional tone, and camera mood matches the brand’s voice and demographic context.\n\n"

                    "### BALANCED CAMERA CONTINUITY RULES (YOU MUST FOLLOW THESE WHILE WRITING THE SCRIPT)\n"
                    "To ensure that the video can be generated smoothly, camera movements must be visually coherent, physically believable, "
                    "and stylistically consistent. Follow these rules carefully:\n\n"

                    "1. Camera movements CAN be dynamic and cinematic, including gentle arcs, dolly moves, push-ins, pullbacks, passes across "
                    "the sofa, subtle rotations, low sweeps, elevated glides, and product-focused reveals.\n\n"

                    "2. However, you are NOT allowed to make abrupt or extreme changes in a single step. Avoid sudden jumps such as:\n"
                    "- wide → close-up\n"
                    "- close-up → wide\n"
                    "- eye-level → top-down\n"
                    "- low-angle → high-angle\n"
                    "- side-view → full-room shot instantly\n\n"

                    "3. If a dramatic angle (close-up, low-angle, elevated, top-down) is required, you MUST transition smoothly using intermediate "
                    "camera positions. Example:\n"
                    "- wide → medium-wide → medium → medium-close → close-up\n"
                    "- normal eye-level → slightly elevated → higher → top-down\n\n"

                    "4. The environment MUST stay consistent across all segments. Do NOT add or remove objects, change furniture layout, alter wall "
                    "decor, lighting direction, or room geometry unless the user explicitly asks for a scene change.\n\n"

                    "5. Every segment must visually connect to the previous one. Each shot must feel like a natural continuation of the previous "
                    "camera position, angle, and direction, preserving spatial consistency. The camera should move as if in real physical space.\n\n"

                    "6. Subtle variations are encouraged—such as minor perspective shifts, closer framing, slight height changes, or gentle movement "
                    "around the product—as long as the scene remains the same.\n\n"

                    "If any part of the script violates the continuity rules, you must rewrite it so it becomes fully compliant.\n\n"

                    "### FOLLOW THE EXAMPLE OUTPUT FORMAT BELOW\n"
                    "## Script Title\n\n"
                    "**Video Length:** 40 seconds\n\n"
                    "**Scene:** A pristine, bustling professional kitchen. Sunlight streams through a large window.\n\n"
                    
                    "**(0–8 seconds)**\n"
                    "**VISUAL:** Close-up shot of a chef's hands, deftly chopping fresh herbs on a wooden cutting board. The movements are precise and "
                    "confident. The scene captures the texture of the herbs and warm morning light.\n\n"

                    "**(8–16 seconds)**\n"
                    "**VISUAL:** The chef smiles subtly while reaching for a jar of Hellmann’s Real Mayonnaise on a clean stainless steel counter, "
                    "softly illuminated by daylight.\n\n"

                    "**(16–24 seconds)**\n"
                    "**VISUAL:** A smooth dollop of mayonnaise is added to a mixing bowl with vibrant, fresh ingredients.\n\n"

                    "**(24–32 seconds)**\n"
                    "**VISUAL:** A seamless montage of dishes showing the versatility of Hellmann’s. The jar stays subtly visible in one of the shots.\n\n"

                    "**(32–40 seconds)**\n"
                    "**VISUAL:** Final hero shot of the Hellmann’s Real Mayonnaise jar centered and glowing under soft diffused light."
                )

        },
        }

    def get(self, agent_name: str) -> dict:
        agent_config = self.config.get(agent_name, {})
        
        if not agent_config:
            raise Exception(f"Agent '{agent_name}' not found in configuration")
        return agent_config


def create_prompt_for_post_and_caption(script: str) -> str:
    return (
        f"Analyse the {script} and give a title to this. "
        "Return ONLY the title text, without any prefixes like 'Title:' or any formatting."
    )


def create_prompt_for_summary_generation(script: str) -> str:
    return (
        f"Analyse the {script} and give a summary to this in less than 300 words. "
        "Return ONLY the summary text, without any prefixes like 'Summary:' or any formatting. "
        "Do not include any duration in the summary. Refer to the script as 'The video'."
    )


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


def generate_prompt_for_product_description():
    return (
        "Write a strictly factual description (around 100 words) of the product shown in the image. "
        "YOU MUST follow these rules without exception:\n\n"

        "1. Describe ONLY what is directly, clearly, and undeniably visible in the image.\n"
        "2. Do NOT guess, assume, infer, or speculate about anything that is not visually confirmed.\n"
        "3. Do NOT mention hidden or internal features—avoid any claims about storage, capacity, materials, mechanisms, electronics, functionality, performance, or how the product is used.\n"
        "4. Do NOT infer product category details beyond what is visually obvious (e.g., do NOT assume a bed has storage, a cabinet has shelves, a device has buttons, etc.).\n"
        "5. Do NOT describe dimensions, weight, durability, material type, wood species, metal type, fabric type, technology, or manufacturing details unless explicitly visible.\n"
        "6. Do NOT add context about lifestyle, intended use, background, lighting, camera, or environment.\n"
        "7. Quote ALL visible text exactly as it appears.\n"
        "8. If a feature is partially visible and cannot be confidently identified, describe it only as a visual shape or surface—never label it with a specific function.\n\n"

        "Your goal is to provide an accurate, objective, observation-only description of the product strictly based on what the image shows—nothing more."
    )


def generate_product_scene_validation_prompt():
    return f"""
        You are validating SCENE CONTINUITY between two images:

        IMAGE 1 = PREVIOUS KEYFRAME  
        IMAGE 2 = NEXT KEYFRAME

        Your ONLY goal is to determine whether IMAGE 2 is a STRICT, PLAUSIBLE, and LOGICAL continuation of IMAGE 1.

        You must judge continuity based ONLY on what is clearly visible.  
        No assumptions. No guesses.

        ------------------------------------------------------------
        ### STRICT RULES FOR CONTINUITY (APPLY ALL)
        The NEXT KEYFRAME is INVALID if ANY of these occur:

        OBJECT-LEVEL CHANGES:
        - Any object visible in IMAGE 1 disappears in IMAGE 2.
        - Any new object appears in IMAGE 2 that was not in IMAGE 1.
        - An object changes shape, size, proportions, texture, or material.
        - Product structure, geometry, branding, or label changes.

        SCENE / ENVIRONMENT CHANGES:
        - Room layout changes (walls, decor, flooring, windows, furniture).
        - Background changes position, scale, or style in a way not caused by camera movement.
        - Lighting changes direction or intensity significantly.
        - Color tone or rendering style changes.

        CAMERA IMPOSSIBILITIES:
        - Jump cuts to totally different angles (low → high, wide → close, side → top).
        - Perspective change too large to be a single smooth camera motion.
        - Framing is inconsistent with any realistic camera move.

        LOGIC BREAKS:
        - People, hands, food items, props move or vanish without explanation.
        - Key objects teleport, rotate, or shift unnaturally.
        - Scene looks like a different rendering or different setup.

        ------------------------------------------------------------
        ### VALID CONTINUATION (RARE — ALL MUST BE TRUE)
        The NEXT KEYFRAME is VALID ONLY IF:
        - It is unmistakably the SAME SCENE and SAME ENVIRONMENT.
        - All objects maintain consistent position and identity.
        - The only differences are those produced by small camera moves:
        - slight pan
        - slight tilt
        - gentle dolly movement
        - slight zoom
        - Lighting remains consistent with the same time and setting.

        ------------------------------------------------------------
        ### FIX SUGGESTION REQUIREMENT
        If the NEXT KEYFRAME is invalid, you MUST give a practical, direct fix:

        - Suggest EXACT camera actions (e.g., “slight pan right”, “zoom-in 10%”, “tilt down slightly”).
        - Describe WHAT must remain in frame.
        - Describe WHAT must be corrected (e.g., “restore missing bowl”, “keep chef in same position”, “preserve table layout”).

        The suggestion MUST be:
        - specific,
        - actionable,
        - tied to the mistake,
        - realistic for image-to-image correction.

        ------------------------------------------------------------
        ### OUTPUT FORMAT (STRICT)
        Return ONLY valid JSON:

        {{
        "is_valid_continuation": true or false,
        "reason": "short explanation of the continuity issue",
        "fix_suggestion": "specific camera movement or framing correction to fix continuity"
        }}
        """


def build_regeneration_prompt(
    segment_prompt: str, 
    reason: str, 
    fix_suggestion: str
) -> str:
    
    regeneration_prompt = f"""
        You are an expert cinematic video creator and continuity editor and are using gemini-2.5-flash-preview model to generate keyframes. 
        Your task is to generate a corrected, highly descriptive keyframe prompt that fixes the continuity error in the failed keyframe.

        You are provided with TWO IMAGES (supplied separately in the API call):
        - IMAGE 1: The correct previous keyframe
        - IMAGE 2: The incorrect failed keyframe
        - IMAGE 3 = PRODUCT IMAGE(for which product focussed video is created)


        --------------------------
        CONTEXT INFORMATION
        --------------------------
        Original Segment Prompt:
        "{segment_prompt}"

        Reason for Failure:
        "{reason}"

        Mandatory Fix Suggestion (MUST be applied):
        "{fix_suggestion}"

        --------------------------
        YOUR TASK
        --------------------------
        1. Visually analyze IMAGE 1 to determine:
        - Camera angle and framing
        - Lighting direction, shadows, environment layout
        - Athlete's exact appearance, wardrobe, pose, and objects in the scene (e.g., bench, treadmill)

        2. Visually analyze IMAGE 2 to understand:
        - What went wrong and what MUST NOT be repeated
        - Which continuity elements were broken

        3. Synthesize:
        - The aesthetic intent of the original segment prompt
        - The spatial and temporal continuity from IMAGE 1
        - The required corrections from the fix suggestion

        4. Create a **single paragraph** describing the corrected keyframe.
        It MUST:
        - Maintain seamless continuity with IMAGE 1
        - Apply the fix suggestion exactly
        - Avoid all issues shown in IMAGE 2
        - Accurately match environment, lighting, and character appearance
        - Include photorealistic directions (“ultra-photorealistic”, “real lens optics”, “natural depth of field”, “no CGI look”)
        - Show a believable temporal progression from the previous keyframe

        --------------------------
        OUTPUT REQUIREMENT
        --------------------------
        Output ONLY the corrected keyframe prompt as one paragraph.
        No explanations, no commentary, no lists.

        Generate the corrected keyframe prompt now.
        """
    return regeneration_prompt.strip()


def update_keyframe_prompt_for_middle_video_generation(segment_video_prompt):
    
    prompt = f"""
        INPUTS
        segment_prompt = {segment_video_prompt}
        IMAGE_1 = previous correct keyframe 
        IMAGE_2 = failed next keyframe 
        IMAGE_3 = product image 


        SYSTEM INSTRUCTIONS (DO NOT EDIT ANYTHING BELOW THIS LINE)
        You must validate scene continuity between IMAGE_1 (previous keyframe) and IMAGE_2 (next keyframe) and then generate a corrected, highly descriptive keyframe prompt for NanoBanana that fixes the continuity issues.
        IMAGE_3 is the product image whose structure, geometry, labels, and identity must remain fully consistent whenever the product is shown.
        You must perform both tasks in one unified step.

        Important: The actual input to NanoBanana will be:
        • KEYFRAME_01 (IMAGE_1)
        • PRODUCT_IMAGE (IMAGE_3)
        NanoBanana will NOT receive IMAGE_2. IMAGE_2 is used only for continuity diagnostics and must not be treated as a visual reference for generation.


        :white_check_mark: CONTINUITY VALIDATION RULES (FROM ORIGINAL PROMPT 01)
        IMAGE_2 is INVALID if ANY of the following occur:

        OBJECT-LEVEL CHANGES
        * Any object visible in IMAGE_1 disappears in IMAGE_2
        * Any new object appears
        * An object changes shape, size, proportions, texture, or material
        * Product structure, geometry, branding, or label changes

        SCENE / ENVIRONMENT CHANGES
        * Room layout changes (walls, décor, flooring, windows, furniture)
        * Background shifts in position, scale, or style NOT caused by camera motion
        * Lighting direction or intensity changes noticeably
        * Color tone or rendering style changes

        CAMERA IMPOSSIBILITIES
        * Jump cuts to totally different angles (low → high, wide → close, side → top)
        * Perspective change too large to be a single smooth camera movement
        * Framing inconsistent with any realistic camera move

        LOGIC BREAKS
        * People, hands, food items, or props move or vanish without explanation
        * Key objects teleport, rotate unnaturally, or shift illogically
        * Scene looks like a different rendering or physical setup


        :dart: VALID CONTINUATION CRITERIA
        IMAGE_2 is valid ONLY IF ALL are true:
        * SAME SCENE and SAME ENVIRONMENT
        * SAME PRODUCT identity and geometry
        * ALL objects maintain consistent position and identity
        * ONLY small camera-based differences allowed:
        * slight pan
        * slight tilt
        * gentle dolly
        * slight zoom
        * Lighting remains consistent with the same time and setting


        :wrench: FIX SUGGESTION REQUIREMENT (FROM PROMPT 01)
        If IMAGE_2 is invalid, internally determine:
        * The exact corrective camera movement
        * What MUST remain in frame
        * What MUST be restored
        * The exact visual correction tied to the continuity issue
        This fix MUST influence your final output.


        :movie_camera: CORRECTED KEYFRAME GENERATION RULES (FROM ORIGINAL PROMPT 02)
        After evaluating continuity and determining the fix:

        1. Analyze IMAGE_1 for:
        * camera angle & framing
        * lighting direction, shadows
        * environment layout
        * subject appearance, wardrobe, pose
        * objects and product placement

        2. Analyze IMAGE_2 to understand:
        * the continuity errors
        * what must NOT be repeated

        3. Synthesize:
        * the intent of the segment_prompt
        * the spatial & temporal continuity from IMAGE_1
        * the corrective fix
        * product identity from IMAGE_3

        4. Produce ONE SINGLE PARAGRAPH describing the corrected next keyframe.
        It MUST:
        * maintain perfect continuity with IMAGE_1
        * apply the fix suggestion exactly
        * avoid all issues seen in IMAGE_2
        * accurately match environment, lighting, subject, wardrobe, props
        * represent a clear progression from IMAGE_1 that advances the story and action described in the segment_prompt, instead of repeating the same moment or composition
        * refer to and visually include the product only if the current moment in the segment_prompt and scene composition naturally require it; whenever the product is shown, its shape, geometry, branding, and labels must remain fully consistent with IMAGE_3
        * use cinematic, photorealistic language:
            ultra-photorealistic, real lens optics, natural depth of field, true-to-life shadows, no CGI look


        :large_blue_square: FINAL OUTPUT FORMAT (REQUESTED BY YOU)
        Your entire output MUST be in the following format:

        INSTRUCTION_TO_NANO: Use PRODUCT_IMAGE (IMAGE_1) and the KEYFRAME_01 (IMAGE_2) as visual references, and use the following description to generate KEYFRAME_02 that continues seamlessly from KEYFRAME_01 for video generation. Include the product only if the scene requires it, and when shown, match the PRODUCT_IMAGE exactly.

        <one single corrected keyframe descriptive paragraph goes here>

        No lists.
        No analysis.
        No steps.
        No JSON.
        No meta commentary.
        No extra text.

        ONLY the instruction line + the corrected paragraph.


        :white_check_mark: END OF FULL COMBINED PROMPT

        """

    return prompt


def update_keyframe_prompt_for_end_video_generation(segment_video_prompt):
    prompt = f"""

        INPUTS (EDIT ONLY THIS BLOCK)
        segment_prompt = {segment_video_prompt}

        IMAGE_1 = previous correct keyframe 
        IMAGE_3 = product image 
        (NO IMAGE_2 PROVIDED — this keyframe must be generated as the FINAL closing frame)


        SYSTEM INSTRUCTIONS (DO NOT EDIT ANYTHING BELOW THIS LINE)
        In this case, there is NO IMAGE_2 (no next keyframe).
        Your task is to generate a NEW FINAL KEYFRAME based entirely on:

        • Continuity from IMAGE_1  
        • Product identity from IMAGE_3 (only when shown)  
        • The narrative and intent of segment_prompt  
        • Ending the video convincingly and cohesively  

        This will be the FINAL FRAME of the video.

        Important: The actual input to NanoBanana will be:
        • KEYFRAME_01 (IMAGE_1)
        • PRODUCT_IMAGE (IMAGE_3)
        You must generate a textual description that NanoBanana will pair with these images. Include or reference the product only if the moment in the segment_prompt naturally requires it; when it appears, its geometry, branding, and identity must match IMAGE_3 exactly.


        :dart: REQUIREMENTS FOR NEW ENDING KEYFRAME (ADAPTED FROM ORIGINAL PROMPTS)

        1. Analyze IMAGE_1 to determine:
        • camera angle & framing  
        • lighting direction, shadows  
        • environment layout  
        • subject appearance, wardrobe, pose  
        • objects and product placement  

        2. Since there is no IMAGE_2:
        • Do NOT attempt continuity correction  
        • Instead, generate a believable FINAL KEYFRAME  
        • The new frame must still look like the same scene, same environment, same lighting  
        • The final composition must feel like a natural visual conclusion  

        3. Synthesize:
        • The ending intent of the segment_prompt  
        • Spatial and temporal continuity from IMAGE_1  
        • Product identity, geometry, labels from IMAGE_3 (only when shown)  
        • Classic cinematic "closing shot" logic  

        4. Produce ONE SINGLE PARAGRAPH describing the final keyframe.
        It MUST:
        • maintain perfect continuity with IMAGE_1  
        • preserve product identity & geometry from IMAGE_3 whenever the product is shown  
        • match environment, lighting, subject, wardrobe, props  
        • look like the natural FINAL concluding moment of the sequence  
        • use cinematic, photorealistic language:
            ultra-photorealistic, real lens optics, natural depth of field,
            true-to-life shadows, no CGI look  
        • include the product only if visually or narratively appropriate in this final moment


        :large_blue_square: FINAL OUTPUT FORMAT (UPDATED FOR "NO END FRAME EXISTS — GENERATE FINAL FRAME")
        Your entire output MUST be in the following format:

        INSTRUCTION_TO_NANO: Use PRODUCT_IMAGE (IMAGE_1) and the KEYFRAME_01 (IMAGE_2) as the only visual references, and use the following description to generate the FINAL KEYFRAME that concludes the video. Include the product only if the final moment requires it, and match its identity exactly when shown.

        <one single detailed final keyframe descriptive paragraph goes here>

        No lists.
        No analysis.
        No steps.
        No JSON.
        No meta commentary.
        No extra text.

        ONLY the instruction line + the final paragraph.
    
    """

    return prompt


def update_keyframe_prompt_for_first_video_generation(segment_video_prompt):
    prompt = f"""
        INPUTS
        segment_prompt = {segment_video_prompt}

        IMAGE_1 = previous correct keyframe 
        IMAGE_3 = product image 
        (NO IMAGE_2 PROVIDED — this keyframe must be generated as the NEXT frame)

        SYSTEM INSTRUCTIONS (DO NOT EDIT ANYTHING BELOW THIS LINE)
        Your task is to generate a NEXT KEYFRAME based entirely on:

        • Continuity from IMAGE_1  
        • Product identity from IMAGE_3 (only when shown)  
        • The narrative and intent of segment_prompt  
        • Ending the video convincingly and cohesively  

        This will be the FINAL FRAME of the video.

        Important: The actual input to NanoBanana will be:
        • KEYFRAME_01 (IMAGE_1)
        • PRODUCT_IMAGE (IMAGE_3)
        You must generate a textual description that NanoBanana will pair with these images. Include or reference the product only if the moment in the segment_prompt naturally requires it; when it appears, its geometry, branding, and identity must match IMAGE_3 exactly.

        🎯 REQUIREMENTS FOR NEW ENDING KEYFRAME (ADAPTED FROM ORIGINAL PROMPTS)

        1. Analyze IMAGE_1 to determine:
        • camera angle & framing  
        • lighting direction, shadows  
        • environment layout  
        • subject appearance, wardrobe, pose  
        • objects and product placement  

        2. Since there is no IMAGE_2:
        • Attempt continuity correction  
        • Instead, generate a believable NEXT KEYFRAME  
        • The new frame must still look like the same scene, same environment, same lighting  
        • The final composition must feel like a natural visual conclusion  

        3. Synthesize:
        • The ending intent of the segment_prompt  
        • Spatial and temporal continuity from IMAGE_1  
        • Product identity, geometry, labels from IMAGE_3 (only when shown)  
        • Classic cinematic "closing shot" logic  

        4. Produce ONE SINGLE PARAGRAPH describing the final keyframe.
        It MUST:
        • maintain perfect continuity with IMAGE_1  
        • preserve product identity & geometry from IMAGE_3 whenever the product is shown  
        • match environment, lighting, subject, wardrobe, props  
        • look like the natural FINAL concluding moment of the sequence  
        • use cinematic, photorealistic language:
            ultra-photorealistic, real lens optics, natural depth of field,
            true-to-life shadows, no CGI look  
        • include the product only if visually or narratively appropriate in this final moment

        FINAL OUTPUT FORMAT (UPDATED FOR "NO END FRAME EXISTS — GENERATE FINAL FRAME")
        Your entire output MUST be in the following format:

        INSTRUCTION_TO_NANO: Use KEYFRAME_01 (IMAGE_1) and PRODUCT_IMAGE (IMAGE_3) as the only visual references, and use the following description to generate the NEXT KEYFRAME for the video which should be little different from IMAGE_1 but is continuous. Include the product only if the next keyframe moment requires it, and match its identity exactly when shown.

        <one single detailed final keyframe descriptive paragraph goes here>

        No lists.
        No analysis.
        No steps.
        No JSON.
        No meta commentary.
        No extra text.

        ONLY the instruction line + the final paragraph.
        """
    return prompt
