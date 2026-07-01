"""App icon generator.

Priority:
  1. If profile.jpg exists in the app root → circular crop + accent border ring
     → saved as app_icon.ico / app_icon.png. (Add your photo in Settings.)
  2. Otherwise → lightning bolt on a violet rounded square (default design).

Re-generated whenever the icon files are missing.
"""

import os

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROFILE_SRC = os.path.join(BASE_DIR, "profile.jpg")
ICO_PATH = os.path.join(DATA_DIR, "app_icon.ico")
PNG_PATH = os.path.join(DATA_DIR, "app_icon.png")

# Default lightning-bolt palette
ACCENT = (108, 92, 231, 255)
ACCENT_DARK = (90, 75, 212, 255)
BOLT = (255, 255, 255, 255)
GLOW = (253, 203, 110, 255)

# Profile-photo palette
BORDER_COLOR = (99, 102, 241, 255)      # indigo border ring
BADGE_BG = (253, 203, 110, 255)         # amber badge circle
BADGE_TEXT = (30, 30, 30, 255)


# ---- lightning-bolt icon (fallback) --------------------------------------

def _draw_bolt(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size * 0.06
    radius = size * 0.24
    d.rounded_rectangle([pad, pad, size - pad, size - pad],
                        radius=radius, fill=ACCENT)
    d.rounded_rectangle([pad, size * 0.52, size - pad, size - pad],
                        radius=radius, fill=ACCENT_DARK)
    pts = [
        (0.56, 0.14), (0.32, 0.55), (0.47, 0.55),
        (0.42, 0.86), (0.70, 0.43), (0.53, 0.43),
    ]
    poly = [(x * size, y * size) for x, y in pts]
    d.polygon(poly, fill=BOLT, outline=GLOW)
    return img


# ---- circular profile photo icon -----------------------------------------

def _circle_mask(size):
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    return mask


def _draw_profile(size):
    """Crop profile.jpg to a circle with an accent border ring."""
    photo = Image.open(PROFILE_SRC).convert("RGBA")

    # 1. Square-crop to the centre
    w, h = photo.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    photo = photo.crop((left, top, left + side, top + side))

    # 2. Resize to (size - 2*border) leaving room for border ring
    border = max(4, size // 16)
    inner = size - 2 * border
    photo = photo.resize((inner, inner), Image.LANCZOS)

    # 3. Apply circular mask
    mask = _circle_mask(inner)
    photo.putalpha(mask)

    # 4. Compose onto a transparent canvas with border ring
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # draw border circle
    ImageDraw.Draw(img).ellipse([0, 0, size - 1, size - 1], fill=BORDER_COLOR)
    # paste photo centred
    img.paste(photo, (border, border), photo)

    return img


# ---- public API ----------------------------------------------------------

def ensure_icon():
    """Create icon files if missing; return (ico_path, png_path)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(ICO_PATH) or not os.path.exists(PNG_PATH):
        if os.path.exists(PROFILE_SRC):
            try:
                master = _draw_profile(256)
            except Exception:
                master = _draw_bolt(256)
        else:
            master = _draw_bolt(256)
        master.save(PNG_PATH)
        master.save(ICO_PATH, sizes=[(256, 256), (128, 128), (64, 64),
                                     (48, 48), (32, 32), (16, 16)])
    return ICO_PATH, PNG_PATH


def get_avatar_image(size=36):
    """Return a PIL Image for the topbar avatar (circular), or None."""
    try:
        if os.path.exists(PROFILE_SRC):
            img = _draw_profile(size * 2)   # 2× for sharpness
        else:
            img = _draw_bolt(size * 2)
        return img.resize((size, size), Image.LANCZOS)
    except Exception:
        return None


if __name__ == "__main__":
    ensure_icon()
    print("Icon generated at", ICO_PATH)
