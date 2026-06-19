from video_utilities.utils import UtilityTools


class ValidationTools:

    @staticmethod
    def validate_nano_banana_chat_response(response):

        status = {"valid": False, "type": None}

        # Check if response from step 1 is not empty str.
        if response == "":
            print("Empty response from step 1")
            status["valid"] = False
            return status

        image = UtilityTools.extract_image_from_chat_response(response)
        text = UtilityTools.exract_text_from_chat_response(response)

        if image:
            status["valid"] = True
            status["type"] = "image"
            status["image"] = image
            return status

        elif text:
            status["valid"] = True
            status["type"] = "text"
            status["text"] = text
            return status

        else:
            print("No image or text found in response from step 1")
            status["valid"] = False
            return status

    @staticmethod
    def validate_segment_key_values(segment_list):
        valid_key_list = [
            "keyframe_number",
            "keyframe_type",
            "keyframe_prompt",
            "video_segment_duration",
            "segment_video_prompt",
        ]

        segment_error_tracker = {
            "number_of_segments": 0,
            "number_of_errors": 0,
            "errored_segment": [],
        }

        segment_error_tracker["number_of_segments"] = len(segment_list)
        for segment_index, segment in enumerate(segment_list):

            for key in segment:
                if key not in valid_key_list:
                    segment_error_tracker["number_of_errors"] += 1
                    segment_error_tracker["errored_segment"].append(segment_index)

        if segment_error_tracker["number_of_errors"] > 0:
            print(f"Number of errors: {segment_error_tracker['number_of_errors']}")
            print(f"Errored segments: {segment_error_tracker['errored_segment']}")
            return False

        print(f"Number of segments: {segment_error_tracker['number_of_segments']}")
        return True

    @staticmethod
    def validate_segment_duration(segment_list, target_duration):
        valid_duration_list = [4, 6, 8]
        total_duration = 0

        for segment in segment_list:

            # Check if segment duration is even
            segment_duration = int(segment["video_segment_duration"])

            if segment_duration % 2 == 1:
                segment_duration += 1

            # Fail fast if not a valid segment duration
            if segment_duration not in valid_duration_list:
                return False

            total_duration += int(segment["video_segment_duration"])

        if total_duration != target_duration:
            total_diff = abs(total_duration - target_duration)

            if not total_diff < 8:
                return False

        return True
