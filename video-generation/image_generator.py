from video_utilities.image_tools import ImageTools
from video_utilities.utils import UtilityTools
from video_utilities.validations import ValidationTools


class ImageGenerator:
    def __init__(self, chat, aspect_ratio):
        self.chat = chat
        self.aspect_ratio = aspect_ratio

    def call_llm_with_prompt_images(
        self,
        agent_name: str,
        agent_variant: str,
        agent_config: dict,
        context_prompt: str,
        pil_images,
        chat
    ):
        agent_prompt_config = agent_config.get(agent_name, {})

        system_prompt = agent_prompt_config.get(agent_variant, "")

        try:
            print(f"Calling {agent_name} agent with image:")
            full_prompt = f"{system_prompt}\n{context_prompt}"

            response = chat.send_message_with_images([full_prompt], pil_images, self.aspect_ratio)

            if not response:
                print(f"Empty response from {agent_name} agent")
                print(f"LLM response: {response}")
                return ""

            print(f"Successfully received response from {agent_name} agent")
            return response

        except Exception as e:
            print(f"API call failed for {agent_name}: {e}")

    def create_image(
        self,
        image_list,
        prompt,
        base_prompt_key,
        chat,
        agent_config,
        segment_index,
    ):
        try:

            # Change the aspect ratio of all of the images
            # corrected_image_list = []

            # for image in image_list:
            #     corrected_image_list.append(
            #         ImageTools.check_and_change_image_aspect_ratio(
            #             image, self.aspect_ratio
            #         )
            #     )

            response = self.call_llm_with_prompt_images(
                "prompt_library",
                base_prompt_key,
                agent_config,
                prompt,
                image_list,
                chat
            )

            # Set image and prompt identifiers
            image_name = str(segment_index)
            prompt_name = image_name

            # Check if response from step 1 is None.
            step_one_status = ValidationTools.validate_nano_banana_chat_response(
                response
            )
          
            if not step_one_status["valid"]:
                return "Invalid response from step 1"

            if base_prompt_key == "direct_single_image_generation":
                #print(f"{step_one_status =}")
                generated_image = step_one_status["image"]

                return generated_image



            elif step_one_status["type"] == "image":
                generated_image = step_one_status["image"]

                return generated_image

            elif step_one_status["type"] == "text":
                prompt = step_one_status["text"]
                
                response = self.call_llm_with_prompt_images(
                    "prompt_library",
                    "direct_image_generation",  # Hardcoded for now as only 2 steps
                    agent_config,
                    prompt,
                    image_list,
                    chat,
                )

                # Check if response from step 2 is None.
                step_two_status = ValidationTools.validate_nano_banana_chat_response(
                    response
                )
                print(
                    f"*******************************\n{step_two_status}\n********************************\n\n\n"
                )

                if not step_two_status["valid"]:
                    return "Invalid response from step 2"

                if step_two_status["type"] == "text":
                    pass

                else:
                    generated_image = step_two_status["image"]

                    return generated_image

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error: {e}")
            return "Error"
