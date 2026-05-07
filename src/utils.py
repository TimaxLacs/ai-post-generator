import re
import os
import logging
from typing import Tuple

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def extract_images(text: str, allowed_dir: str = "images") -> Tuple[str, list[str]]:
    pattern = r"\[image:\s*(.+?)\]"
    images = re.findall(pattern, text)
    clean_text = re.sub(pattern, "", text).replace("  ", " ").strip()
    
    safe_images = []
    base_dir = os.path.abspath(allowed_dir)
    
    for img in images:
        abs_img_path = os.path.abspath(img)
        # Prevent LFI by ensuring the resolved path starts with the allowed base directory
        if not abs_img_path.startswith(base_dir):
            raise ValueError(f"Path traversal detected: {img}")
        if os.path.exists(abs_img_path):
            safe_images.append(abs_img_path)
            
    return clean_text, safe_images
