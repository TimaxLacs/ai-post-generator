import pytest
import os
from src.utils import extract_images, setup_logging

def test_extract_images_safe_path(tmp_path):
    # Setup allowed directory
    allowed_dir = tmp_path / "images"
    allowed_dir.mkdir()
    safe_img = allowed_dir / "safe.png"
    safe_img.touch()
    
    text = f"Hello [image: {safe_img}]"
    clean_text, images = extract_images(text, allowed_dir=str(allowed_dir))
    
    assert clean_text == "Hello"
    assert len(images) == 1
    assert images[0] == str(safe_img)

def test_extract_images_lfi_prevention(tmp_path):
    allowed_dir = tmp_path / "images"
    allowed_dir.mkdir()
    
    unsafe_img = tmp_path / "secret.txt"
    unsafe_img.touch()
    
    text = f"Hacked [image: ../secret.txt]"
    
    with pytest.raises(ValueError, match="Path traversal detected"):
        extract_images(text, allowed_dir=str(allowed_dir))
