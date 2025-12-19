from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import requests
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class WatermarkService:
    
    # ============================================
    # WATERMARK SIZE SETTINGS - ADJUST HERE!
    # ============================================
    LOGO_SIZE_PERCENT = 0.05  # Logo is 10% of image height (increased since no text)
    BACKGROUND_OPACITY = 200  # 0-255, higher = more opaque
    PADDING = 25  # Distance from corner
    ADD_BACKGROUND = False  # Set to False for transparent background behind logo
    
    @staticmethod
    def add_watermark(
        image_path: str, 
        output_path: str, 
        text: str = "Pre-Wedding AI",  # Not used anymore, kept for compatibility
        logo_path: str = None
    ) -> str:
        """
        Add logo-only watermark to image
        
        CUSTOMIZATION SETTINGS (adjust at top of class):
        - LOGO_SIZE_PERCENT: Logo height as % of image (0.08 = 8%, 0.12 = 12%)
        - BACKGROUND_OPACITY: 0-255 (0=transparent, 255=solid)
        - PADDING: Distance from corner in pixels
        - ADD_BACKGROUND: True/False - whether to add dark background behind logo
        """
        try:
            logger.info(f"🎨 Adding logo watermark to image...")
            logger.info(f"  Input: {image_path}")
            logger.info(f"  Output: {output_path}")
            logger.info(f"  Logo: {logo_path if logo_path else 'None'}")
            
            # Load main image (supports both local and S3)
            if image_path.startswith('http'):
                logger.debug("Downloading image from S3...")
                response = requests.get(image_path)
                image = Image.open(BytesIO(response.content))
            else:
                logger.debug("Loading local image...")
                image = Image.open(image_path)
            
            width, height = image.size
            logger.info(f"  Image size: {width}x{height}")
            
            # Convert to RGBA for transparency support
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Create transparent overlay
            overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            # ============================================
            # LOGO WATERMARK
            # ============================================
            if not logo_path:
                raise ValueError("Logo path is required for watermark")
            
            logger.info(f"📸 Loading logo from: {logo_path}")
            
            # Verify logo exists
            if not os.path.exists(logo_path):
                logger.error(f"❌ Logo file not found: {logo_path}")
                raise FileNotFoundError(f"Logo not found: {logo_path}")
            
            # Load logo
            logo = Image.open(logo_path)
            logger.info(f"✅ Logo loaded successfully: {logo.size}, mode: {logo.mode}")
            
            # Convert to RGBA
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # ============================================
            # CALCULATE LOGO SIZE
            # ============================================
            logo_height = int(height * WatermarkService.LOGO_SIZE_PERCENT)
            aspect_ratio = logo.width / logo.height
            logo_width = int(logo_height * aspect_ratio)
            
            # Resize logo
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            logger.info(f"  Resized logo to: {logo_width}x{logo_height}")
            
            # ============================================
            # POSITION LOGO (bottom-right corner)
            # ============================================
            padding = WatermarkService.PADDING
            logo_x = width - logo_width - padding
            logo_y = height - logo_height - padding
            
            # ============================================
            # OPTIONAL: DRAW BACKGROUND BEHIND LOGO
            # ============================================
            if WatermarkService.ADD_BACKGROUND:
                bg_padding = 10
                draw.rounded_rectangle(
                    [
                        logo_x - bg_padding,
                        logo_y - bg_padding,
                        logo_x + logo_width + bg_padding,
                        logo_y + logo_height + bg_padding
                    ],
                    radius=12,
                    fill=(0, 0, 0, WatermarkService.BACKGROUND_OPACITY)
                )
                logger.info("  Added background behind logo")
            
            # ============================================
            # PASTE LOGO
            # ============================================
            overlay.paste(logo, (logo_x, logo_y), logo)
            
            logger.info(f"✅ Logo watermark applied: {logo_width}x{logo_height} at ({logo_x}, {logo_y})")
            
            # Composite overlay onto image
            watermarked = Image.alpha_composite(image, overlay)
            
            # Convert back to RGB for saving
            if watermarked.mode == 'RGBA':
                watermarked = watermarked.convert('RGB')
            
            # Save watermarked image
            watermarked.save(output_path, quality=95, optimize=True)
            logger.info(f"✅ Watermarked image saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Watermark failed: {str(e)}")
            logger.exception("Full watermark error:")
            raise Exception(f"Failed to add watermark: {str(e)}")
    
    @staticmethod
    def add_diagonal_pattern(
        image_path: str, 
        output_path: str,
        text: str = "FREE VERSION"
    ) -> str:
        """
        Add diagonal watermark pattern across entire image
        More aggressive watermark for free users
        """
        try:
            # Load image
            if image_path.startswith('http'):
                response = requests.get(image_path)
                image = Image.open(BytesIO(response.content))
            else:
                image = Image.open(image_path)
            
            width, height = image.size
            
            # Create transparent overlay
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            overlay = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Font
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                    int(width * 0.04)
                )
            except:
                font = ImageFont.load_default()
            
            # Draw diagonal pattern
            spacing = 200
            for i in range(-height, width, spacing):
                for j in range(0, height, int(spacing * 0.75)):
                    draw.text(
                        (i, j), 
                        text, 
                        fill=(255, 255, 255, 60),
                        font=font
                    )
            
            # Composite
            watermarked = Image.alpha_composite(image, overlay)
            
            # Convert to RGB
            if watermarked.mode == 'RGBA':
                watermarked = watermarked.convert('RGB')
            
            watermarked.save(output_path, quality=95, optimize=True)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to add diagonal watermark: {str(e)}")