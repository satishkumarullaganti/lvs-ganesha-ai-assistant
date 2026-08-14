"""
Digital Annaprasada Coupon Generator
=====================================
Generates a single admit-1 coupon image styled to match the
physical "Food Coupon - ADMIT ONLY - 1" cards used last year:
- LVS Excellency oval logo at top
- "Food Coupon" title
- "ADMIT ONLY - 1"
- QR code (encodes the /verify/{coupon_id} URL)
- Serial number

Each coupon represents exactly ONE person, matching the
physical coupon precedent - a family booking for N members
gets N separate coupon images, one per person, instead of a
single shared QR covering the whole group.
"""

import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

COUPON_FOLDER = "static/coupons"
LOGO_PATH = "frontend/assets/images/lvs_logo.png"

# Fonts are bundled directly in the project (backend/assets/fonts/)
# rather than relying on the OS having DejaVu installed - this is
# what broke on Windows (the old path only existed on Linux). The
# path is built relative to this file's own location so it works
# the same regardless of the working directory the app is run from.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(_THIS_DIR, "assets", "fonts")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")


def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        # Last-resort fallback so coupon generation never hard-crashes
        # the booking flow even if a font file is ever missing/moved.
        return ImageFont.load_default()


GANESHA_PATH = "frontend/assets/images/app_logo.png"

os.makedirs(COUPON_FOLDER, exist_ok=True)

CANVAS_WIDTH = 700
CANVAS_HEIGHT = 1000

# Colors matched to the physical coupon's yellow/orange gradient
GRADIENT_TOP = (255, 213, 79)      # warm yellow
GRADIENT_BOTTOM = (255, 152, 0)    # LVS orange (#ff9800)
TITLE_COLOR = (183, 28, 28)        # deep red, matches "Food Coupon" script text
ADMIT_COLOR = (33, 33, 33)         # near-black
SERIAL_COLOR = (255, 255, 255)


def _vertical_gradient(width, height, top_color, bottom_color):

    base = Image.new("RGB", (width, height), top_color)
    draw = ImageDraw.Draw(base)

    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return base


def _circular_crop(image, target_diameter):

    # Crop to a centered square first, then apply a circular mask
    square_size = min(image.width, image.height)
    left = (image.width - square_size) // 2
    top = (image.height - square_size) // 2
    square = image.crop((left, top, left + square_size, top + square_size))

    square = square.resize((target_diameter, target_diameter), Image.LANCZOS)

    mask = Image.new("L", (target_diameter, target_diameter), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, target_diameter, target_diameter], fill=255)

    result = Image.new("RGBA", (target_diameter, target_diameter))
    result.paste(square, (0, 0), mask)

    return result


def _draw_centered_text(draw, text, y, font, fill, canvas_width):

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (canvas_width - text_width) / 2
    draw.text((x, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def generate_annaprasada_coupon(
    coupon_id,
    serial_number,
    name,
    members,
    verify_url
):
    """
    Creates a coupon image styled after the physical
    "Food Coupon" cards, and saves it to disk. Covers the
    full booking (all members on this one coupon, same as
    the existing booking/redemption logic) - only the
    visual template is styled after the physical design.
    Returns the relative file path (for serving via StaticFiles).
    """

    canvas = _vertical_gradient(
        CANVAS_WIDTH, CANVAS_HEIGHT, GRADIENT_TOP, GRADIENT_BOTTOM
    )
    draw = ImageDraw.Draw(canvas)

    # --------------------------------------------
    # Logo badge (white oval behind the LVS logo,
    # matching the physical coupon's white badge)
    # --------------------------------------------
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo_target_width = 380
    logo_ratio = logo_target_width / logo.width
    logo_target_height = int(logo.height * logo_ratio)
    logo = logo.resize((logo_target_width, logo_target_height), Image.LANCZOS)

    badge_padding = 20
    badge_w = logo_target_width + badge_padding * 2
    badge_h = logo_target_height + badge_padding * 2
    badge_x = (CANVAS_WIDTH - badge_w) // 2
    badge_y = 40

    draw.ellipse(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        fill=(255, 255, 255)
    )

    canvas.paste(
        logo,
        (badge_x + badge_padding, badge_y + badge_padding),
        logo
    )

    # --------------------------------------------
    # Ganesha badge - small circular accent placed
    # near the top, alongside the main LVS Excellency
    # logo (festival branding touch, on top of the
    # society logo which stays the primary identity)
    # --------------------------------------------
    ganesha_diameter = 130

    ganesha_raw = Image.open(GANESHA_PATH).convert("RGBA")
    ganesha_circle = _circular_crop(ganesha_raw, ganesha_diameter - 10)

    ganesha_x = badge_x + badge_w - (ganesha_diameter // 2)
    ganesha_y = badge_y - (ganesha_diameter // 4)

    # White ring behind it for a clean badge edge,
    # matching the style of the main logo badge
    draw.ellipse(
        [
            ganesha_x, ganesha_y,
            ganesha_x + ganesha_diameter, ganesha_y + ganesha_diameter
        ],
        fill=(255, 255, 255),
        outline=(255, 152, 0),
        width=4
    )

    canvas.paste(
        ganesha_circle,
        (ganesha_x + 5, ganesha_y + 5),
        ganesha_circle
    )

    current_y = badge_y + badge_h + 30

    # --------------------------------------------
    # "Food Coupon" title
    # --------------------------------------------
    title_font = _load_font(FONT_BOLD, 54)
    current_y += _draw_centered_text(
        draw, "Food Coupon", current_y, title_font, TITLE_COLOR, CANVAS_WIDTH
    )
    current_y += 20

    # --------------------------------------------
    # Members covered by this coupon (this coupon
    # covers the WHOLE booking, not just 1 person -
    # matches the app's existing partial-redemption
    # logic, unlike the physical "ADMIT ONLY - 1" cards)
    # --------------------------------------------
    admit_font = _load_font(FONT_BOLD, 38)
    members_text = f"Members : {members}"
    current_y += _draw_centered_text(
        draw, members_text, current_y, admit_font, ADMIT_COLOR, CANVAS_WIDTH
    )
    current_y += 30

    # --------------------------------------------
    # Participant name
    # --------------------------------------------
    name_font = _load_font(FONT_REGULAR, 28)
    current_y += _draw_centered_text(
        draw, name, current_y, name_font, ADMIT_COLOR, CANVAS_WIDTH
    )
    current_y += 30

    # --------------------------------------------
    # QR code
    # --------------------------------------------
    qr_img = qrcode.make(verify_url).convert("RGB")
    qr_size = 320
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    qr_x = (CANVAS_WIDTH - qr_size) // 2

    # White backing card behind the QR for scan contrast
    qr_padding = 16
    draw.rectangle(
        [
            qr_x - qr_padding, current_y - qr_padding,
            qr_x + qr_size + qr_padding, current_y + qr_size + qr_padding
        ],
        fill=(255, 255, 255)
    )

    canvas.paste(qr_img, (qr_x, current_y))
    current_y += qr_size + qr_padding + 30

    # --------------------------------------------
    # Coupon ID (shown instead of a plain serial
    # number, since this is what actually gets
    # looked up if a volunteer needs to search for
    # this booking manually)
    # --------------------------------------------
    serial_font = _load_font(FONT_BOLD, 30)
    serial_text = f"{coupon_id}"
    _draw_centered_text(
        draw, serial_text, current_y, serial_font, SERIAL_COLOR, CANVAS_WIDTH
    )

    # --------------------------------------------
    # Save
    # --------------------------------------------
    file_name = f"{coupon_id}.png"
    file_path = os.path.join(COUPON_FOLDER, file_name)
    canvas.save(file_path)

    return file_path