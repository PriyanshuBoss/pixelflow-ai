
import fal_client

class FluxClient:

    def __init__(self):
        pass

    def upscale_image_by_topaz(self, image_url):
       
        try:
            result = fal_client.run(
                "fal-ai/topaz/upscale/image",
                arguments={
                    "image_url": f"{image_url}", 
                    "scale": 4.0,                                   
                    "model": "High Fidelity V2",                            
                    "face_enhance": True                            
                }
            )

            print(f"response from flux:{result}")
            
            return result.get('image',{}).get('url')

        except Exception as e:
            print(f"[ERROR] FLUX API call failed: {e}")
            return None
