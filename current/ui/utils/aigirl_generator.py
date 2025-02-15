import asyncio
from playwright.async_api import async_playwright
import logging
import os
import requests
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

WEBSHARE_API_KEY = os.getenv("WEBSHARE_API_KEY")
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
WEBSHARE_API_URL = "https://proxy.webshare.io/api/proxy/list/"

async def get_proxies():
    """Fetch a list of proxies from Webshare"""
    try:
        headers = {
            "Authorization": f"Token {WEBSHARE_API_KEY}"
        }
        response = requests.get(WEBSHARE_API_URL, headers=headers)
        if response.status_code == 200:
            proxies = response.json().get('results', [])
            # Format proxies as ip:port
            formatted_proxies = [f"{proxy['proxy_address']}:{proxy['ports']['http']}" for proxy in proxies]
            return formatted_proxies
        else:
            logging.error(f"Failed to fetch proxies from Webshare: {response.status_code}")
            return []
    except Exception as e:
        logging.error(f"Error fetching proxies from Webshare: {str(e)}")
        return []

async def test_proxy(proxy_str: str) -> bool:
    """Test if a proxy is working"""
    try:
        proxy_parts = proxy_str.split(":")
        if len(proxy_parts) != 2:
            logging.warning(f"Invalid proxy format: {proxy_str}")
            return False
        
        ip, port = proxy_parts
        
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(proxy={
                    "server": f"http://{ip}:{port}",
                    "username": PROXY_USERNAME,
                    "password": PROXY_PASSWORD
                }, timeout=20000)
                page = await browser.new_page()
                await page.goto("https://www.example.com", timeout=10000)  # Shorter timeout
                await browser.close()
                return True
            except Exception as e:
                logging.warning(f"Proxy {proxy_str} failed: {str(e)}")
                if 'net::ERR_TUNNEL_CONNECTION_FAILED' in str(e):
                    logging.warning("Tunnel connection failed, likely a bad proxy.")
                return False
    except Exception as e:
        logging.warning(f"Error testing proxy {proxy_str}: {str(e)}")
        return False

async def generate_image_async(prompt: str, save_path: str) -> str:
    """Generate character image using Flux AI generator with proxy support"""
    if not prompt:
        logging.error("No prompt provided for image generation")
        return None
        
    try:
        logging.info(f"Generating image with prompt: {prompt}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to generator
            await page.goto("https://ai-girl.site/flux-ai-image-generator", timeout=30000)
            logging.info("Page loaded")
            
            # Wait for input field and enter prompt
            input_field = await page.wait_for_selector('input[data-testid="textbox"]', timeout=5000)
            await input_field.fill(prompt)
            logging.info("Entered prompt")
            
            # Click generate button
            await page.click('button:has-text("Run")')
            logging.info("Started generation")
            
            # Wait for image generation
            await page.wait_for_timeout(16000)
            
            # Look for generated image
            image = await page.wait_for_selector(
                'img.svelte-1pijsyv[src^="https://black-forest-labs-flux-1-schnell.hf.space/file=/tmp/gradio/"]',
                timeout=35000
            )
            
            if not image:
                raise Exception("No image element found after generation")
                
            img_src = await image.get_attribute('src')
            logging.info(f"Found image source: {img_src}")
            
            # Download and save image
            img_response = await page.request.get(img_src)
            img_data = await img_response.body()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(img_data)
                
            await browser.close()
            logging.info(f"Image saved to: {save_path}")
            return save_path
            
    except Exception as e:
        logging.error(f"Error generating image: {e}")
        return None

def generate_image(prompt: str, save_path: str) -> str:
    """Synchronous wrapper for generate_image_async"""
    try:
        print(f"Starting image generation with prompt: {prompt}")
        result = asyncio.get_event_loop().run_until_complete(
            generate_image_async(prompt, save_path)
        )
        print(f"Image generation completed: {result}")
        return result
    except Exception as e:
        logging.error(f"Error in generate_image: {e}")
        return None
