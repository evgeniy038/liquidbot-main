"""
Dynamic image generator for promotion notifications.

Creates personalized congratulation images with usernames overlaid on background templates.
Uses Saans font and role-based subtitle text.

Banner 1 & 2: Centered single-line layout "Congratulations @Username"
Banner 3, 4, 5: Two-line left-aligned layout (from Figma JSON)
"""

import asyncio
import io
import random
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont

from src.utils import get_logger

logger = get_logger(__name__)

# Default paths
ASSETS_DIR = Path("assets/promotion_banners")
FONTS_DIR = Path("assets/fonts")

# Color from Figma: #EDEDFF
TEXT_COLOR = (237, 237, 255)  # Light purple-white

# Original Figma canvas size (for scaling calculations)
FIGMA_WIDTH = 2560
FIGMA_HEIGHT = 1920

# Target Discord embed size
TARGET_WIDTH = 640
TARGET_HEIGHT = 360

# Scale factor (Figma -> Discord)
SCALE_FACTOR = TARGET_WIDTH / FIGMA_WIDTH

# Event winner role ID - special subtitle text
EVENT_WINNER_ROLE_ID = "1443237596384985263"

# Role ID to name mapping for subtitle text
ROLE_NAMES = {
    # Community roles
    "1436827617993953361": "Wave",
    "1436827751922274386": "Tide",
    "1436827711288119466": "Current",
    "1436825727029874698": "All-in Liquid",
    "1436826732043698370": "Founding Droplets",
    "1436826786821312663": "Liquid Frens",
    "1443238384234659881": "Tsunami",
    "1443237596384985263": "Event Winner",
    # Guild - Traders
    "1449055127049605312": "Tide",
    "1449055171685515354": "Degen",
    "1449055325020754100": "Speculator",
    # Guild - Content
    "1449054897486954506": "Drip",
    "1449054975107010673": "Frame",
    "1449055051829084353": "Orator",
    # Guild - Designers
    "1449054607899758726": "Ink",
    "1449054761650225244": "Sketch",
    "1449054806038675569": "Sculptor",
}


def get_subtitle_text(role_id: str, role_name: str = None) -> str:
    """Get subtitle text based on role ID."""
    if role_id == EVENT_WINNER_ROLE_ID:
        return "You have won a community event"
    else:
        name = role_name or ROLE_NAMES.get(role_id, "member")
        return f"You have been promoted to {name}"


class PromotionImageGenerator:
    """
    Generates personalized promotion images with username overlay.
    
    Banner 1 & 2: Centered single-line layout
    Banner 3, 4, 5: Two-line left-aligned layout (from Figma JSON)
    """
    
    def __init__(
        self,
        assets_dir: Optional[Path] = None,
        fonts_dir: Optional[Path] = None,
    ):
        self.assets_dir = assets_dir or ASSETS_DIR
        self.fonts_dir = fonts_dir or FONTS_DIR
        
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        
        # Template configurations
        # Banner 1 & 2: single_line_centered
        # Banner 3, 4, 5: two_line_left (from JSON specs)
        self.templates = [
            {
                # Banner 1: Centered single-line
                "filename": "banner_1.png",
                "layout": "single_line_centered",
                "main_text": {
                    "top": 1450,
                    "font_size": 180,
                },
                "subtitle": {
                    "top": 1750,
                    "font_size": 80,
                    "opacity": 0.7,
                },
            },
            {
                # Banner 2: Centered single-line
                "filename": "banner_2.png",
                "layout": "single_line_centered",
                "main_text": {
                    "top": 1400,
                    "font_size": 180,
                },
                "subtitle": {
                    "top": 1700,
                    "font_size": 80,
                    "opacity": 0.7,
                },
            },
            {
                # Banner 3: Two-line left-aligned (from JSON)
                "filename": "banner_3.png",
                "layout": "two_line_left",
                "congratulations": {
                    "top": 1209.55,
                    "left": 172,
                    "font_size": 222.19,
                },
                "username": {
                    "top": 1449.55,
                    "left": 172,
                    "font_size": 222.19,
                },
                "subtitle": {
                    "top": 1736,
                    "left": 172,
                    "font_size": 87.86,
                    "opacity": 0.7,
                },
            },
            {
                # Banner 4: Two-line left-aligned (from JSON)
                "filename": "banner_4.png",
                "layout": "two_line_left",
                "congratulations": {
                    "top": 1209.55,
                    "left": 172,
                    "font_size": 222.19,
                },
                "username": {
                    "top": 1449.55,
                    "left": 172,
                    "font_size": 222.19,
                },
                "subtitle": {
                    "top": 1736,
                    "left": 172,
                    "font_size": 87.86,
                    "opacity": 0.7,
                },
            },
            {
                # Banner 5: Two-line left-aligned (from JSON)
                "filename": "banner_5.png",
                "layout": "two_line_left",
                "congratulations": {
                    "top": 1209.55,
                    "left": 172,
                    "font_size": 222.19,
                },
                "username": {
                    "top": 1449.55,
                    "left": 172,
                    "font_size": 222.19,
                },
                "subtitle": {
                    "top": 1736,
                    "left": 172,
                    "font_size": 87.86,
                    "opacity": 0.7,
                },
            },
        ]
        
        self._template_cache = {}
        self._font_cache = {}
    
    def _get_font(self, size: int, weight: str = "medium") -> ImageFont.FreeTypeFont:
        """Get Saans or fallback font with caching."""
        cache_key = (size, weight)
        
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        font = None
        
        font_names = {
            "medium": ["Saans-TRIAL-Regular.otf", "Saans-Regular.otf", "ShareTech-Regular.ttf", "Inter-Medium.ttf"],
            "bold": ["Saans-TRIAL-Regular.otf", "Saans-Regular.otf", "ShareTech-Regular.ttf", "Inter-Bold.ttf"],
            "variable": ["Saans-TRIAL-Regular.otf", "Saans-Regular.otf", "ShareTech-Regular.ttf", "Inter-Variable.ttf"],
        }
        
        for font_name in font_names.get(weight, font_names["medium"]):
            font_path = self.fonts_dir / font_name
            if font_path.exists():
                try:
                    font = ImageFont.truetype(str(font_path), size)
                    logger.debug(f"loaded_font: {font_name} size={size}")
                    break
                except Exception as e:
                    logger.warning(f"failed_to_load_font: {font_name} - {e}")
                    continue
        
        if font is None:
            system_fonts = ["arial.ttf", "Arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]
            for sys_font in system_fonts:
                try:
                    font = ImageFont.truetype(sys_font, size)
                    logger.debug(f"loaded_system_font: {sys_font}")
                    break
                except Exception:
                    continue
        
        if font is None:
            logger.warning("using_default_pil_font")
            font = ImageFont.load_default()
        
        self._font_cache[cache_key] = font
        return font
    
    def _load_template(self, filename: str) -> Optional[Image.Image]:
        """Load template image with caching."""
        if filename in self._template_cache:
            return self._template_cache[filename].copy()
        
        template_path = self.assets_dir / filename
        
        if not template_path.exists():
            logger.warning(f"template_not_found: {template_path}")
            return None
        
        try:
            image = Image.open(template_path).convert("RGBA")
            self._template_cache[filename] = image
            logger.info(f"loaded_template: {filename} size={image.size}")
            return image.copy()
        except Exception as e:
            logger.error(f"failed_to_load_template: {e}")
            return None
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template filenames."""
        available = []
        for template in self.templates:
            template_path = self.assets_dir / template["filename"]
            if template_path.exists():
                available.append(template["filename"])
        return available
    
    async def generate_promotion_image(
        self,
        username: str,
        template_index: Optional[int] = None,
        role_id: Optional[str] = None,
        role_name: Optional[str] = None,
    ) -> Optional[io.BytesIO]:
        """Generate personalized promotion image (async wrapper)."""
        return await asyncio.to_thread(
            self._generate_promotion_image_sync,
            username,
            template_index,
            role_id,
            role_name,
        )

    def _generate_promotion_image_sync(
        self,
        username: str,
        template_index: Optional[int] = None,
        role_id: Optional[str] = None,
        role_name: Optional[str] = None,
    ) -> Optional[io.BytesIO]:
        """Generate personalized promotion image (synchronous implementation)."""
        available = self.get_available_templates()
        
        if not available:
            logger.warning("no_templates_available")
            return self._generate_fallback_image(username, role_id, role_name)
        
        if template_index is not None and 0 <= template_index < len(self.templates):
            template_config = self.templates[template_index]
            if template_config["filename"] not in available:
                template_config = self.templates[0]
        else:
            available_configs = [t for t in self.templates if t["filename"] in available]
            template_config = random.choice(available_configs)
        
        image = self._load_template(template_config["filename"])
        if image is None:
            return self._generate_fallback_image(username, role_id, role_name)
        
        img_width, img_height = image.size
        scale_x = img_width / FIGMA_WIDTH
        scale_y = img_height / FIGMA_HEIGHT
        scale = min(scale_x, scale_y)
        
        draw = ImageDraw.Draw(image)
        
        layout = template_config.get("layout", "two_line_left")
        
        if layout == "single_line_centered":
            # Banner 1 & 2: Draw "Congratulations @Username" CENTERED
            main_config = template_config["main_text"]
            main_font_size = int(main_config["font_size"] * scale)
            main_font = self._get_font(main_font_size, "medium")
            main_y = int(main_config["top"] * scale)
            
            combined_text = f"congratulations @{username}"
            
            bbox = draw.textbbox((0, 0), combined_text, font=main_font)
            text_width = bbox[2] - bbox[0]
            main_x = (img_width - text_width) // 2
            
            draw.text((main_x, main_y), combined_text, font=main_font, fill=TEXT_COLOR)
            
            # Centered subtitle
            if "subtitle" in template_config:
                subtitle_config = template_config["subtitle"]
                subtitle_font_size = int(subtitle_config["font_size"] * scale)
                subtitle_font = self._get_font(subtitle_font_size, "medium")
                subtitle_y = int(subtitle_config["top"] * scale)
                
                opacity = subtitle_config.get("opacity", 0.7)
                subtitle_color = (TEXT_COLOR[0], TEXT_COLOR[1], TEXT_COLOR[2], int(255 * opacity))
                
                subtitle_text = get_subtitle_text(role_id or "", role_name)
                
                bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
                subtitle_width = bbox[2] - bbox[0]
                subtitle_x = (img_width - subtitle_width) // 2
                
                draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=subtitle_color)
        
        else:
            # Banner 3, 4, 5: Two-line LEFT-ALIGNED layout
            congrats_config = template_config["congratulations"]
            congrats_font_size = int(congrats_config["font_size"] * scale)
            congrats_font = self._get_font(congrats_font_size, "medium")
            congrats_x = int(congrats_config["left"] * scale)
            congrats_y = int(congrats_config["top"] * scale)
            
            draw.text((congrats_x, congrats_y), "Congratulations", font=congrats_font, fill=TEXT_COLOR)
            
            username_config = template_config["username"]
            username_font_size = int(username_config["font_size"] * scale)
            username_font = self._get_font(username_font_size, "medium")
            username_x = int(username_config["left"] * scale)
            username_y = int(username_config["top"] * scale)
            
            draw.text((username_x, username_y), f"@{username}", font=username_font, fill=TEXT_COLOR)
            
            # Left-aligned subtitle
            if "subtitle" in template_config:
                subtitle_config = template_config["subtitle"]
                subtitle_font_size = int(subtitle_config["font_size"] * scale)
                subtitle_font = self._get_font(subtitle_font_size, "medium")
                subtitle_x = int(subtitle_config["left"] * scale)
                subtitle_y = int(subtitle_config["top"] * scale)
                
                opacity = subtitle_config.get("opacity", 0.7)
                subtitle_color = (TEXT_COLOR[0], TEXT_COLOR[1], TEXT_COLOR[2], int(255 * opacity))
                
                subtitle_text = get_subtitle_text(role_id or "", role_name)
                
                draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=subtitle_color)
        
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        
        logger.info(
            "promotion_image_generated",
            username=username,
            template=template_config["filename"],
            layout=layout,
            role_id=role_id,
            image_size=image.size,
        )
        
        return buffer
    
    def _generate_fallback_image(
        self,
        username: str,
        role_id: Optional[str] = None,
        role_name: Optional[str] = None,
    ) -> io.BytesIO:
        """Generate a simple fallback image when no templates are available."""
        width, height = TARGET_WIDTH, TARGET_HEIGHT
        image = Image.new("RGBA", (width, height), (20, 20, 28, 255))
        draw = ImageDraw.Draw(image)
        
        for y in range(height):
            for x in range(width):
                current = image.getpixel((x, y))
                blue_factor = (x / width) * 0.15 + (1 - y / height) * 0.1
                new_color = (current[0], current[1], min(int(current[2] + 40 * blue_factor), 255), 255)
                image.putpixel((x, y), new_color)
        
        title_font = self._get_font(36, "medium")
        subtitle_font = self._get_font(16, "medium")
        
        combined_text = f"congratulations @{username}"
        bbox = draw.textbbox((0, 0), combined_text, font=title_font)
        title_width = bbox[2] - bbox[0]
        title_x = (width - title_width) // 2
        
        draw.text((title_x, 140), combined_text, font=title_font, fill=TEXT_COLOR)
        
        subtitle_text = get_subtitle_text(role_id or "", role_name)
        bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = bbox[2] - bbox[0]
        subtitle_x = (width - subtitle_width) // 2
        
        draw.text((subtitle_x, 200), subtitle_text, font=subtitle_font, fill=(TEXT_COLOR[0], TEXT_COLOR[1], TEXT_COLOR[2], 178))
        
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        
        return buffer
    
    def generate_test_images(self, output_dir: Optional[Path] = None) -> List[Path]:
        """Generate test images for all available templates."""
        output_dir = output_dir or Path("assets/test_outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_cases = [
            ("CryptoKing", EVENT_WINNER_ROLE_ID),
            ("LiquidMaster", "1436827617993953361"),
            ("WaterDrop99", "1443238384234659881"),
            ("TradePro", "1449055325020754100"),
            ("DiamondHands", "1436826732043698370"),
        ]
        
        generated_files = []
        
        for i, template in enumerate(self.templates):
            if not (self.assets_dir / template["filename"]).exists():
                continue
            
            username, role_id = test_cases[i % len(test_cases)]
            image_buffer = self._generate_promotion_image_sync(
                username=username,
                template_index=i,
                role_id=role_id,
            )
            
            if image_buffer:
                output_path = output_dir / f"test_banner_{i + 1}_{username}.png"
                with open(output_path, "wb") as f:
                    f.write(image_buffer.read())
                generated_files.append(output_path)
                logger.info(f"generated_test_image: {output_path}")
        
        fallback_buffer = self._generate_fallback_image("EventUser", EVENT_WINNER_ROLE_ID)
        fallback_path = output_dir / "test_fallback_event_winner.png"
        with open(fallback_path, "wb") as f:
            f.write(fallback_buffer.read())
        generated_files.append(fallback_path)
        
        fallback_buffer = self._generate_fallback_image("PromoUser", "1443238384234659881")
        fallback_path = output_dir / "test_fallback_promotion.png"
        with open(fallback_path, "wb") as f:
            f.write(fallback_buffer.read())
        generated_files.append(fallback_path)
        
        return generated_files


_generator: Optional[PromotionImageGenerator] = None


def get_image_generator() -> PromotionImageGenerator:
    """Get singleton image generator instance."""
    global _generator
    if _generator is None:
        _generator = PromotionImageGenerator()
    return _generator


if __name__ == "__main__":
    generator = get_image_generator()
    print(f"Available templates: {generator.get_available_templates()}")
    
    test_files = generator.generate_test_images()
    print(f"\nGenerated {len(test_files)} test images:")
    for f in test_files:
        print(f"  - {f}")
