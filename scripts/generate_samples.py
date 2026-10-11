"""Generate diverse sample logos for examples/ directory."""

from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFilter

examples_dir = Path(__file__).resolve().parent / "examples"
examples_dir.mkdir(parents=True, exist_ok=True)

# 1. Geometric Tech Logo (Sharp / Polygon mode)
# Crisp hexagon with inner isometric facet cube
def create_geometric_logo():
    size = (400, 400)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    cx, cy = 200, 200
    r = 140

    # Calculate 6 vertices of hexagon
    hex_pts = [
        (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        for a in range(30, 390, 60)
    ]

    # Draw outer hexagon
    d.polygon(hex_pts, fill=(30, 41, 59, 255))

    # Inner isometric cube facets
    inner_r = 90
    top_pt = (cx, cy - inner_r)
    bot_pt = (cx, cy + inner_r)
    left_pt = (cx - inner_r * math.cos(math.radians(30)), cy - inner_r * math.sin(math.radians(30)) + inner_r * 0.5)
    right_pt = (cx + inner_r * math.cos(math.radians(30)), cy - inner_r * math.sin(math.radians(30)) + inner_r * 0.5)
    center_pt = (cx, cy)

    # Top face
    d.polygon([center_pt, (cx - inner_r * math.cos(math.radians(30)), cy - inner_r * 0.5), top_pt, (cx + inner_r * math.cos(math.radians(30)), cy - inner_r * 0.5)], fill=(14, 165, 233, 255))
    # Left face
    d.polygon([center_pt, (cx - inner_r * math.cos(math.radians(30)), cy - inner_r * 0.5), (cx - inner_r * math.cos(math.radians(30)), cy + inner_r * 0.5), (cx, cy + inner_r)], fill=(2, 132, 199, 255))
    # Right face
    d.polygon([center_pt, (cx, cy + inner_r), (cx + inner_r * math.cos(math.radians(30)), cy + inner_r * 0.5), (cx + inner_r * math.cos(math.radians(30)), cy - inner_r * 0.5)], fill=(3, 105, 161, 255))

    img.save(examples_dir / "geometric_logo.png", format="PNG")
    print("Created geometric_logo.png")

# 2. Smooth Circular Badge Emblem (Smooth preset)
def create_smooth_badge():
    size = (400, 400)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    cx, cy = 200, 200

    # Outer circle
    d.ellipse([30, 30, 370, 370], fill=(220, 38, 38, 255))
    # Inner ring (white)
    d.ellipse([55, 55, 345, 345], fill=(255, 255, 255, 255))
    # Dark red inner disc
    d.ellipse([70, 70, 330, 330], fill=(185, 28, 28, 255))
    # Gold circle
    d.ellipse([95, 95, 305, 305], fill=(245, 158, 11, 255))

    # Center white star
    star_r_out = 70
    star_r_in = 28
    star_pts = []
    for i in range(10):
        r = star_r_out if i % 2 == 0 else star_r_in
        angle = math.radians(i * 36 - 90)
        star_pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    d.polygon(star_pts, fill=(255, 255, 255, 255))

    img.save(examples_dir / "smooth_badge.png", format="PNG")
    print("Created smooth_badge.png")

# 3. Modern Shield Tech Logo (Logo preset)
def create_tech_shield():
    size = (400, 400)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    d = ImageDraw.Draw(img)

    shield_pts = [
        (200, 40),
        (340, 90),
        (320, 240),
        (200, 360),
        (80, 240),
        (60, 90),
    ]
    # Shield base
    d.polygon(shield_pts, fill=(79, 70, 229, 255))

    # Inner shield accent
    inner_shield = [
        (200, 75),
        (310, 115),
        (295, 230),
        (200, 325),
        (105, 230),
        (90, 115),
    ]
    d.polygon(inner_shield, fill=(99, 102, 241, 255))

    # Center lightning / energy bolt
    bolt_pts = [
        (215, 100),
        (160, 205),
        (205, 205),
        (185, 300),
        (245, 185),
        (200, 185),
    ]
    d.polygon(bolt_pts, fill=(251, 191, 36, 255))

    img.save(examples_dir / "tech_shield.png", format="PNG")
    print("Created tech_shield.png")

# 4. Retro Crest Logo with JPEG compression artifacts (Testing --denoise)
def create_retro_crest():
    size = (400, 400)
    img = Image.new("RGB", size, (248, 250, 252))
    d = ImageDraw.Draw(img)

    # Dark blue diamond
    d.polygon([(200, 50), (350, 200), (200, 350), (50, 200)], fill=(30, 58, 138))
    # Emerald inner diamond
    d.polygon([(200, 85), (315, 200), (200, 315), (85, 200)], fill=(5, 150, 105))
    # Center cream circle
    d.ellipse([140, 140, 260, 260], fill=(254, 243, 199))
    # Inner dark emblem
    d.rectangle([180, 160, 220, 240], fill=(30, 58, 138))
    d.rectangle([160, 180, 240, 220], fill=(30, 58, 138))

    # Save as JPEG with moderate quality to introduce compression artifacts
    img.save(examples_dir / "retro_crest.jpg", format="JPEG", quality=65)
    print("Created retro_crest.jpg")

# 5. Transparent Abstract Icon (Testing --keep-alpha)
def create_transparent_icon():
    size = (360, 360)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 3 overlapping circular petals
    # Petal 1: Coral
    d.ellipse([60, 60, 220, 220], fill=(244, 63, 94, 255))
    # Petal 2: Amber
    d.ellipse([140, 60, 300, 220], fill=(245, 158, 11, 255))
    # Petal 3: Violet
    d.ellipse([100, 130, 260, 290], fill=(139, 92, 246, 255))

    img.save(examples_dir / "transparent_icon.png", format="PNG")
    print("Created transparent_icon.png")

if __name__ == "__main__":
    create_geometric_logo()
    create_smooth_badge()
    create_tech_shield()
    create_retro_crest()
    create_transparent_icon()
    print("All sample logos generated successfully in examples/!")
