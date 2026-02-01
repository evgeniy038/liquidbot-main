"""
Test script for promotion image generator with role-based text.
Banner 1 & 2: Centered single-line layout
Banner 3, 4, 5: Two-line left-aligned layout (from JSON)

Images are resized to 640x360 for faster generation.
"""

import io
import random
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageDraw, ImageFont

# Default paths
ASSETS_DIR = Path("assets/promotion_banners")
FONTS_DIR = Path("assets/fonts")

# Color from Figma: #EDEDFF
TEXT_COLOR = (237, 237, 255)  # Light purple-white

# Original Figma canvas size (for scaling calculations)
FIGMA_WIDTH = 2560
FIGMA_HEIGHT = 1920

# Event winner role ID
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

# Template configurations
# Banner 1 & 2: single_line_centered = "Congratulations @Username" centered
# Banner 3, 4, 5: two_line_left = "Congratulations" + "@Username" on separate lines, left-aligned
TEMPLATES = [
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
        # Banner 2: Centered single-line (changed!)
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
        # Banner 4: Two-line left-aligned (from JSON - changed!)
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


def get_font(size: int):
    """Get Saans or fallback font."""
    saans_fonts = ["Saans-TRIAL-Regular.otf", "Saans-Regular.otf"]
    for font_name in saans_fonts:
        font_path = FONTS_DIR / font_name
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), size)
            except Exception as e:
                print(f"   ⚠️ Failed to load {font_name}: {e}")
    
    font_path = FONTS_DIR / "ShareTech-Regular.ttf"
    if font_path.exists():
        try:
            return ImageFont.truetype(str(font_path), size)
        except Exception:
            pass
    
    for sys_font in ["arial.ttf", "Arial.ttf", "segoeui.ttf"]:
        try:
            return ImageFont.truetype(sys_font, size)
        except Exception:
            continue
    
    return ImageFont.load_default()


def get_subtitle_text(role_id: str) -> str:
    """Get subtitle text based on role ID."""
    if role_id == EVENT_WINNER_ROLE_ID:
        return "You have won a community event"
    else:
        role_name = ROLE_NAMES.get(role_id, "member")
        return f"You have been promoted to {role_name}"


def generate_promotion_image(
    username: str,
    template_config: dict,
    role_id: str = None,
) -> Optional[io.BytesIO]:
    """Generate personalized promotion image."""
    template_path = ASSETS_DIR / template_config["filename"]
    
    if not template_path.exists():
        print(f"   ⚠️ Template not found: {template_path}")
        return None
    
    try:
        image = Image.open(template_path).convert("RGBA")
    except Exception as e:
        print(f"   ❌ Failed to load template: {e}")
        return None
    
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
        main_font = get_font(main_font_size)
        main_y = int(main_config["top"] * scale)
        
        combined_text = f"Congratulations @{username}"
        
        bbox = draw.textbbox((0, 0), combined_text, font=main_font)
        text_width = bbox[2] - bbox[0]
        main_x = (img_width - text_width) // 2
        
        draw.text((main_x, main_y), combined_text, font=main_font, fill=TEXT_COLOR)
        
        # Centered subtitle
        if "subtitle" in template_config:
            subtitle_config = template_config["subtitle"]
            subtitle_font_size = int(subtitle_config["font_size"] * scale)
            subtitle_font = get_font(subtitle_font_size)
            subtitle_y = int(subtitle_config["top"] * scale)
            
            opacity = subtitle_config.get("opacity", 0.7)
            subtitle_color = (TEXT_COLOR[0], TEXT_COLOR[1], TEXT_COLOR[2], int(255 * opacity))
            
            subtitle_text = get_subtitle_text(role_id or EVENT_WINNER_ROLE_ID)
            
            bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = bbox[2] - bbox[0]
            subtitle_x = (img_width - subtitle_width) // 2
            
            draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=subtitle_color)
    
    else:
        # Banner 3, 4, 5: Two-line LEFT-ALIGNED layout
        congrats_config = template_config["congratulations"]
        congrats_font_size = int(congrats_config["font_size"] * scale)
        congrats_font = get_font(congrats_font_size)
        congrats_x = int(congrats_config["left"] * scale)
        congrats_y = int(congrats_config["top"] * scale)
        
        draw.text((congrats_x, congrats_y), "Congratulations", font=congrats_font, fill=TEXT_COLOR)
        
        username_config = template_config["username"]
        username_font_size = int(username_config["font_size"] * scale)
        username_font = get_font(username_font_size)
        username_x = int(username_config["left"] * scale)
        username_y = int(username_config["top"] * scale)
        
        draw.text((username_x, username_y), f"@{username}", font=username_font, fill=TEXT_COLOR)
        
        # Left-aligned subtitle
        if "subtitle" in template_config:
            subtitle_config = template_config["subtitle"]
            subtitle_font_size = int(subtitle_config["font_size"] * scale)
            subtitle_font = get_font(subtitle_font_size)
            subtitle_x = int(subtitle_config["left"] * scale)
            subtitle_y = int(subtitle_config["top"] * scale)
            
            opacity = subtitle_config.get("opacity", 0.7)
            subtitle_color = (TEXT_COLOR[0], TEXT_COLOR[1], TEXT_COLOR[2], int(255 * opacity))
            
            subtitle_text = get_subtitle_text(role_id or EVENT_WINNER_ROLE_ID)
            
            draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=subtitle_color)
    
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    
    return buffer


def generate_fallback_image(username: str, role_id: str = None) -> io.BytesIO:
    """Generate fallback image when no templates available."""
    width, height = 640, 360
    image = Image.new("RGBA", (width, height), (20, 20, 28, 255))
    draw = ImageDraw.Draw(image)
    
    for y in range(height):
        for x in range(width):
            current = image.getpixel((x, y))
            blue_factor = (x / width) * 0.15 + (1 - y / height) * 0.1
            new_color = (current[0], current[1], min(int(current[2] + 40 * blue_factor), 255), 255)
            image.putpixel((x, y), new_color)
    
    title_font = get_font(36)
    subtitle_font = get_font(16)
    
    combined_text = f"Congratulations @{username}"
    bbox = draw.textbbox((0, 0), combined_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    
    draw.text((text_x, 140), combined_text, font=title_font, fill=TEXT_COLOR)
    
    subtitle_text = get_subtitle_text(role_id or EVENT_WINNER_ROLE_ID)
    bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = bbox[2] - bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    
    draw.text((subtitle_x, 200), subtitle_text, font=subtitle_font, fill=(TEXT_COLOR[0], TEXT_COLOR[1], TEXT_COLOR[2], 178))
    
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    
    return buffer


def generate_single_banner(banner_number: int, username: str = "Username", role_id: str = None):
    """Generate a single banner for quick testing."""
    if banner_number < 1 or banner_number > 5:
        print(f"❌ Banner number must be 1-5, got {banner_number}")
        return
    
    template = TEMPLATES[banner_number - 1]
    output_dir = Path("assets/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🎨 Generating banner_{banner_number}...")
    
    image_buffer = generate_promotion_image(
        username=username,
        template_config=template,
        role_id=role_id or EVENT_WINNER_ROLE_ID,
    )
    
    if image_buffer:
        output_path = output_dir / f"test_banner_{banner_number}_{username}.png"
        with open(output_path, "wb") as f:
            f.write(image_buffer.read())
        print(f"✅ Saved: {output_path}")
        return output_path
    else:
        print("❌ Failed to generate image")
        return None


def main():
    print("=" * 60)
    print("🎨 Promotion Image Generator - Test v5")
    print("   Banner 1 & 2: Centered | Banner 3, 4, 5: Left-aligned")
    print("=" * 60)
    
    available = []
    for template in TEMPLATES:
        template_path = ASSETS_DIR / template["filename"]
        if template_path.exists():
            available.append(template["filename"])
    
    print(f"\n📁 Available templates: {len(available)}")
    for t in available:
        print(f"   ✓ {t}")
    
    print(f"\n🔤 Fonts directory: {FONTS_DIR.absolute()}")
    saans_path = FONTS_DIR / "Saans-TRIAL-Regular.otf"
    if saans_path.exists():
        print(f"   ✓ Saans-TRIAL-Regular.otf found!")
    else:
        print(f"   ⚠️ Saans-TRIAL-Regular.otf NOT found")
    
    test_cases = [
        ("CryptoKing", EVENT_WINNER_ROLE_ID, "Event Winner"),
        ("LiquidMaster", "1436827617993953361", "Wave"),
        ("WaterDrop99", "1443238384234659881", "Tsunami"),
        ("TradePro", "1449055325020754100", "Speculator"),
        ("DiamondHands", "1436826732043698370", "Founding Droplets"),
    ]
    
    print("\n🎨 Generating test images...")
    output_dir = Path("assets/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for i, template in enumerate(TEMPLATES):
        if template["filename"] not in available:
            continue
        
        username, role_id, role_name = test_cases[i % len(test_cases)]
        image_buffer = generate_promotion_image(
            username=username,
            template_config=template,
            role_id=role_id,
        )
        
        if image_buffer:
            output_path = output_dir / f"test_banner_{i + 1}_{username}.png"
            with open(output_path, "wb") as f:
                f.write(image_buffer.read())
            generated_files.append(output_path)
            layout_type = "centered" if template.get("layout") == "single_line_centered" else "left-aligned"
            print(f"   → {output_path.name} ({layout_type}, role: {role_name})")
    
    print("\n📦 Generating fallback images...")
    
    fallback_buffer = generate_fallback_image("EventUser", EVENT_WINNER_ROLE_ID)
    fallback_path = output_dir / "test_fallback_event_winner.png"
    with open(fallback_path, "wb") as f:
        f.write(fallback_buffer.read())
    generated_files.append(fallback_path)
    print(f"   → {fallback_path.name}")
    
    fallback_buffer = generate_fallback_image("PromoUser", "1443238384234659881")
    fallback_path = output_dir / "test_fallback_promotion.png"
    with open(fallback_path, "wb") as f:
        f.write(fallback_buffer.read())
    generated_files.append(fallback_path)
    print(f"   → {fallback_path.name}")
    
    print(f"\n✅ Generated {len(generated_files)} images in: {output_dir.absolute()}")
    
    print("\n" + "=" * 60)
    print("📋 Quick test commands:")
    print("=" * 60)
    print("  python scripts/test_banner_simple.py --banner 2 --user TestUser")
    print("  python scripts/test_banner_simple.py --banner 4 --user TestUser")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and "--banner" in sys.argv:
        try:
            idx = sys.argv.index("--banner")
            banner_num = int(sys.argv[idx + 1])
            
            username = "Username"
            if "--user" in sys.argv:
                user_idx = sys.argv.index("--user")
                username = sys.argv[user_idx + 1]
            
            generate_single_banner(banner_num, username)
        except (IndexError, ValueError):
            print("Usage: python scripts/test_banner_simple.py --banner <1-5> [--user <name>]")
    else:
        main()
