# test_watermark.py
from pathlib import Path
from app.services.watermark_service import WatermarkService
import logging

logging.basicConfig(level=logging.INFO)

# Paths
test_image = "template_previews/template59.png"  # Use any test image
output_image = "test_watermarked.png"
logo_path = "static/logo.png"

# Check if logo exists
if Path(logo_path).exists():
    print(f"✅ Logo found at: {Path(logo_path).absolute()}")
else:
    print(f"❌ Logo NOT found at: {Path(logo_path).absolute()}")
    print("Searching for logo...")
    for p in Path(".").rglob("logo.png"):
        print(f"  Found: {p.absolute()}")

# Test watermark
try:
    WatermarkService.add_watermark(
        test_image,
        output_image,
        text="Test Watermark",
        logo_path=str(Path(logo_path).absolute()) if Path(logo_path).exists() else None
    )
    print(f"✅ Watermark created: {output_image}")
except Exception as e:
    print(f"❌ Error: {e}")