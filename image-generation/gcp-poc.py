import os
import requests
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional
from urllib.parse import urljoin # <-- This is needed for URL correction

# --- Configuration ---
# *** FIX: DEFINE THE VARIABLE HERE ***
PRODUCT_URL = "https://www.wakefit.co/pillows-and-cushions/super-soft-pillow/WSSPD" 
MODEL_NAME = "gemini-2.5-flash"

# --- 1. Define the Desired Output Structure using Pydantic ---
class ProductInfo(BaseModel):
    """A structured model for extracted product data."""
    product_name: str = Field(description="The full, official name of the product.")
    category: str = Field(description="The top-level category (e.g., Electronics, Clothing, Home Goods).")
    sub_category: Optional[str] = Field(description="The more specific sub-category (e.g., Headphones, T-shirts, Coffee Makers).")
    # IMPROVED DESCRIPTION FOR THE MODEL
    image_url: str = Field(description="The direct URL (must start with http or https) of the main, high-resolution product image on the page.")
    
# --- 2. Function to Fetch Web Content ---
def fetch_webpage_content(url: str) -> Optional[str]:
    """Fetches the raw text content from a given URL."""
    print(f"--- 🌐 Fetching content from: {url} ---")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        return response.text 
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch the URL content. Status: {e}")
        return None

# --- 3. Main Extraction Function ---
def extract_product_data(url: str):
    """Fetches content and uses Gemini to extract structured product info."""
    if not os.getenv("GEMINI_API_KEY"):
        print("FATAL ERROR: Please set the GEMINI_API_KEY environment variable.")
        return

    try:
        client = genai.Client()
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize Gemini client. Check API key. Error: {e}")
        return

    # STEP A: Fetch the content
    page_content = fetch_webpage_content(url)
    if not page_content:
        return

    # STEP B: Construct the prompt
    content_snippet = page_content[:10000] 
    prompt = (
        "Analyze the following raw webpage content (HTML/Text). "
        "Extract the product's name, its primary category, its specific sub-category, "
        "and the **absolute, complete image URL** that can be used directly for download. "
        "The image URL must be a complete URL starting with 'http' or 'https'. "
        "Return the result STRICTLY as a JSON object."
        f"\n\n--- WEBPAGE CONTENT SNIPPET ---\n\n{content_snippet}..."
    )
    
    print("Sending content to Gemini for structured extraction...")

    # STEP C: Configure the request for structured JSON output
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ProductInfo,
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt,
            config=config
        )

        structured_data: ProductInfo = response.parsed
        
        # --- KEY FIX: URL RESOLUTION ---
        # This corrects relative URLs (starting with /) and protocol-relative URLs (starting with //)
        corrected_image_url = urljoin(url, structured_data.image_url)
        structured_data.image_url = corrected_image_url

        print("\n--- ✅ Extraction Complete ---")
        print(f"Source URL:     {url}")
        print("---------------------------------")
        print(f"Product Name:   {structured_data.product_name}")
        print(f"Category:       {structured_data.category}")
        print(f"Sub-Category:   {structured_data.sub_category}")
        print(f"Image URL:      {structured_data.image_url}") # Will show the corrected URL
        print("---------------------------------")
        
    except Exception as e:
        print(f"\nAPI Error: Failed to get structured response from Gemini. ({e})")


if __name__ == "__main__":
    # The variable is now defined at the top of the file, so this works:
    extract_product_data(PRODUCT_URL)