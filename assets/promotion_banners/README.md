# Promotion Banner Templates

This folder contains background templates for personalized promotion images.

## How to Export from Figma

1. **Open your Figma design** with the 5 banner variants

2. **Remove the text layer** with "@Username" temporarily (or hide it)
   - The text will be added dynamically by the bot

3. **Select each frame/banner** one by one

4. **Export settings:**
   - Format: **PNG**
   - Scale: **1x** (or 2x for higher quality)
   - Background: Keep the dark background

5. **Name the files exactly:**
   - `banner_1.png`
   - `banner_2.png`
   - `banner_3.png`
   - `banner_4.png`
   - `banner_5.png`

6. **Place files in this folder** (`assets/promotion_banners/`)

## Template Configuration

Each template in `src/moderation/image_generator.py` has settings for:
- `title_position` - Where "Congratulations" text appears (x, y)
- `username_position` - Where "@Username" text appears (x, y)
- `text_color` - RGB color tuple (255, 255, 255) for white
- `center_align` - If True, text is centered on the X position

## Adjusting Text Position

If text doesn't align properly with your design:

1. Open `src/moderation/image_generator.py`
2. Find the `templates` list
3. Adjust `title_position` and `username_position` for each banner

Example:
```python
{
    "filename": "banner_1.png",
    "title_position": (50, 180),      # Lower X = more left, Lower Y = more up
    "username_position": (50, 240),   
    "text_color": (255, 255, 255),
    "title_font_size": 36,
    "username_font_size": 48,
},
```

## Adding Custom Fonts

1. Download a font (e.g., Inter, Outfit, Roboto) from Google Fonts
2. Place `.ttf` files in `assets/fonts/`
3. Recommended names:
   - `Inter-Regular.ttf`
   - `Inter-Bold.ttf`
   - `Outfit-Regular.ttf`
   - `Outfit-Bold.ttf`

## Testing

Run the test script to generate a sample image:
```bash
python -c "from src.moderation.image_generator import get_image_generator; g = get_image_generator(); img = g.generate_promotion_image('TestUser'); open('test_promotion.png', 'wb').write(img.read()) if img else print('No templates found')"
```

## Fallback

If no templates are found, the system generates a simple dark gradient background with the text.
