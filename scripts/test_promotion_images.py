"""
Test script for promotion image generator.
Run this to generate sample images with all banners.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.moderation.image_generator import get_image_generator


def main():
    print("=" * 50)
    print("Promotion Image Generator - Test")
    print("=" * 50)
    
    generator = get_image_generator()
    
    # Check available templates
    available = generator.get_available_templates()
    print(f"\n📁 Available templates: {len(available)}")
    for t in available:
        print(f"   ✓ {t}")
    
    if not available:
        print("\n⚠️  No templates found!")
        print("   Make sure banner_1.png through banner_5.png are in:")
        print("   assets/promotion_banners/")
        print("\n   Generating fallback image only...")
    
    # Generate test images
    print("\n🎨 Generating test images...")
    output_dir = Path("assets/test_outputs")
    test_files = generator.generate_test_images(output_dir)
    
    print(f"\n✅ Generated {len(test_files)} images in: {output_dir.absolute()}")
    for f in test_files:
        print(f"   → {f.name}")
    
    print("\n" + "=" * 50)
    print("Done! Open the test_outputs folder to see the results.")
    print("=" * 50)


if __name__ == "__main__":
    main()
