
import os
import requests
import json
import boto3
import requests
import uuid

from io import BytesIO

class BrandFetchApi:

    def __init__(self, input_data):
        self.input_data = input_data
        self.website_url = input_data.get('website_url')
        
        self.s3_client = boto3.client('s3')
        self.bucket = os.getenv('BUCKET', 'staging-gaana')

    def _cal_brand_data_from_api(self):
       
        
        print(f"[INFO] Starting API request for domain: {self.website_url}")
        
        url = f"https://api.brandfetch.io/v2/brands/{self.website_url}/"
        print(f"[INFO] Request URL: {url}")
        
        headers = {
            'Authorization': f"Bearer {os.getenv('BRAND_FETCH_API_KEY')}"
        }
        print(f"[INFO] Headers prepared with API key")
        
        try:
            print(f"[INFO] Sending GET request to Brandfetch API...")
            response = requests.get(url, headers=headers)
            
            print(f"[INFO] Response status code: {response.status_code}")
            print(f"[INFO] Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            print(f"[SUCCESS] API request successful!")
            
            json_data = response.json()
            print(f"[INFO] JSON response parsed successfully")
            print(f"[INFO] Response data keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dictionary'}")
            
            return json_data
            
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP Error occurred: {e}")
            print(f"[ERROR] Response content: {response.text if 'response' in locals() else 'No response'}")
            
            return None
        
        except requests.exceptions.ConnectionError as e:
            print(f"[ERROR] Connection Error: {e}")
            
            return None
        except requests.exceptions.Timeout as e:
            print(f"[ERROR] Timeout Error: {e}")
            
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request Exception: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON Decode Error: {e}")
            print(f"[ERROR] Raw response content: {response.text if 'response' in locals() else 'No response'}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return None
        
    
    
    def generate_font_url(self, font_data):
        """Generate URL for a font based on its origin"""
        
        if font_data.get("origin") == "google":
           
            font_family = font_data.get("originId", font_data.get("name", ""))
            weights = font_data.get("weights", [])
            weight_param = ":wght@" + ";".join(map(str, weights)) if weights else ""
            
            return f"https://fonts.googleapis.com/css2?family={font_family}{weight_param}&display=swap"
        
        else:
            return ""
        
    def add_urls_to_fonts(self, response):
        fonts_raw_list = response.get("fonts", [])

        default_sizes = {
            "title": 28,
            "subtitle": 20,
            "body": 16
        }

        roboto_defaults = {
            "font": "Roboto",
            "weight": "normal",
            "url": "https://fonts.google.com/specimen/Roboto"
        }

        fonts_list = []

        for font in fonts_raw_list:
            
            if font.get("origin") == "google":
                fonts_list.append(font)

        font_lookup = {f["name"]: f for f in fonts_list}

        fonts = {}
        font_map = {}

        for font_type in ["title", "subtitle", "body"]:
            matched_font = next((f for f in fonts_list if f.get("type") == font_type), None)

            if matched_font:
                font_name = matched_font.get("name", roboto_defaults["font"])
                font_weight = matched_font.get("weight", "normal")
                font_data = font_lookup.get(font_name, {})
                font_url = self.generate_font_url(font_data)
            else:
                font_name = roboto_defaults["font"]
                font_weight = roboto_defaults["weight"]
                font_url = roboto_defaults["url"]

            if font_name not in font_map:
                font_map[font_name] = font_url

            fonts[font_type] = {
                "font": font_name,
                "weight": font_weight,
                "size": default_sizes[font_type],
                "url": font_url
            }
        
        fonts.update({
            'font_map': font_map
        })

        return fonts
        
    def _transform_brandfetch_response(self, response):
       
        logos = self.upload_logos_to_s3(response.get('logos',[]), self.input_data.get('brand_id', uuid.uuid4()))

        colors = [
            {"name": color.get("type", "brand"), "color": color["hex"]}
            for color in response.get("colors", [])
        ]

        
        fonts = self.add_urls_to_fonts(response)

        return {
            "name": f"{response.get('name')} Brand Kit",
            "logos": logos,
            "colors": colors,
            "fonts": fonts
        }
    
    
    def upload_file_object(self, source, object_name: str, image_format: str) -> str:
        
        content_types = {
            'svg': 'image/svg+xml',
            'png': 'image/png', 
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'webp': 'image/webp',
            'gif': 'image/gif',
            'bmp': 'image/bmp'
        }
        
        content_type = content_types.get(image_format.lower(), 'image/jpeg')
        
        if isinstance(source, BytesIO):
            file_object = source
        else:
            response = requests.get(source, stream=True, timeout=30)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: Failed to download image")
            file_object = BytesIO(response.content)

        extra_args = {"ContentType": content_type}
        
        if image_format.lower() == 'svg':
            extra_args.update({
                "CacheControl": "public, max-age=31536000",
                "ContentDisposition": "inline"
            })

        self.s3_client.upload_fileobj(
            file_object,
            self.bucket,
            object_name,
            ExtraArgs=extra_args
        )
        
        return f"https://{self.bucket}.s3.amazonaws.com/{object_name}"
    
    
    def upload_logos_to_s3(self, logos, brand_id):
        s3_urls = []

        for logo in logos:
            if logo.get("type") != "logo":
                continue

            formats = logo.get("formats", [])
            png_format = None
            svg_format = None

            for fmt in formats:
                if fmt.get("format") == "png":
                    png_format = fmt
                
                elif fmt.get("format") == "svg":
                    svg_format = fmt
            try:
                if png_format:
                   
                    src_url = png_format.get("src")
                    
                    if not src_url:
                        continue
                    
                    object_name = f"assets/brand_kit_automation/{brand_id}/{uuid.uuid4()}.png"
                    print(f"Uploading PNG: {object_name}")
                    
                    s3_url = self.upload_file_object(src_url, object_name, "png")
                    s3_urls.append(s3_url)
                    
                    break

                elif svg_format:
                    
                    src_url = svg_format.get("src")
                    
                    if not src_url:
                        continue
                    
                    object_name = f"assets/brand_kit_automation/{brand_id}/{uuid.uuid4()}.svg"
                    s3_url = self.upload_file_object(src_url, object_name, "svg")
                    s3_urls.append(s3_url)
                    
                    break

                else:
                   
                    if formats:
                        selected_format = formats[0]
                        src_url = selected_format.get("src")
                        image_format = selected_format.get("format", "unknown")
                        
                        if not src_url:
                            continue
                        
                        object_name = f"assets/brand_kit_automation/{brand_id}/{uuid.uuid4()}.{image_format}"
                        print(f"Uploading fallback format: {object_name}")
                        s3_url = self.upload_file_object(src_url, object_name, image_format)
                        s3_urls.append(s3_url)
                        
                        break

            except Exception as e:
                print(f"Error uploading logo: {e}")
                continue
        
        print(s3_urls)
        return s3_urls
    
    def get_brand_data(self):

        if not self.website_url:
            print("Error website url not provided")
            
            return {'error_message': "Error website url not provided"}

        response = self._cal_brand_data_from_api()
        
        print(f"response from brand fetch:{response}")

        if response:
            brand_data = self._transform_brandfetch_response(response)
        else:
            brand_data = {'error_message':f"Brand fetch api fail for {self.website_url}"}

        return brand_data

