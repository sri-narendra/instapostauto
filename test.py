import os
from dotenv import load_dotenv
from posting.instapost import has_instagram_api_config, upload_carousel

load_dotenv()

if not has_instagram_api_config():
    print("Set ZERNIO_API_KEY in .env")
    exit(1)

IMAGE_PATH = "pic.png"
CAPTION = "Test post via Zernio MCP 🚀"

if not os.path.isfile(IMAGE_PATH):
    print(f"Image not found: {IMAGE_PATH}")
    exit(1)

print("Uploading via Zernio MCP...")
result = upload_carousel([IMAGE_PATH], caption=CAPTION)
print(f"Result: {result}")
