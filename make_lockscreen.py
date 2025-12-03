#!/usr/bin/env python3
"""
make_lockscreen.py
Full Telegram bot that accepts a wallpaper, composites it into a phone-frame PNG,
draws date/time (India timezone by default), and returns the final image.

Requirements:
  - python-telegram-bot==20.4
  - Pillow
  - pytz
"""

import logging
import os
from datetime import datetime

import pytz
from PIL import Image, ImageDraw, ImageFont, ImageStat
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -----------------------
# Configuration
# -----------------------
BOT_TOKEN = "7764742692:AAHUJ8V1utjXASJNx4UClh8wQAaT4_EC-QY"   # <- replace with your bot token
FRAME_FILE = "phone_frame.png"      # your transparent mockup (must be in project folder)
OUTPUT_FILE = "final_output.jpg"

# fonts (place these TTF files in ./fonts/)
FONT_DATE = "fonts/Roboto-Regular.ttf"
FONT_TIME = "fonts/Roboto-Black.ttf"

# Screen area fallback (used if frame has no transparency):
# If your frame has transparency these values are unused.
FALLBACK_SCREEN_X = 80
FALLBACK_SCREEN_Y = 120
FALLBACK_SCREEN_W = 880
FALLBACK_SCREEN_H = 1900

# timezone for dates (change if needed)
TIMEZONE = "Asia/Kolkata"

# logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# -----------------------
# Utility functions
# -----------------------
def safe_load_font(path: str, size: int):
    """Try loading a TTF/OTF font; fall back to default PIL font."""
    try:
        return ImageFont.truetype(path, size=size)
    except Exception as e:
        logger.warning("Could not load font '%s' (%s). Falling back to default.", path, e)
        return ImageFont.load_default()


def get_transparent_bbox(frame_rgba: Image.Image):
    """
    Return bounding box (left, top, right, bottom) of transparent area
    inside the frame. If none found, return None.
    """
    if frame_rgba.mode != "RGBA":
        frame_rgba = frame_rgba.convert("RGBA")
    alpha = frame_rgba.split()[-1]
    bbox = alpha.getbbox()  # bounding box of non-zero alpha
    # getbbox returns bbox of non-zero alpha (opaque region).
    # We need the inner hole (transparent area), so invert logic:
    # If alpha has opaque border and transparent interior, alpha.getbbox() will return full bbox.
    # To detect inner transparent area, we create an inverted alpha and check its bbox.
    try:
        # Create inverted alpha: transparent -> white, opaque -> black
        # Pillow ImageOps.invert works on 'L' mode; but avoid dependency; compute manually:
        bw = alpha.point(lambda p: 255 - p)
        inv_bbox = bw.getbbox()
        if inv_bbox:
            # inv_bbox is bounding box of transparent region(s)
            return inv_bbox  # left, top, right, bottom
    except Exception:
        pass
    return None


def get_screen_area(frame: Image.Image):
    """
    Try to detect the transparent screen area inside the frame.
    Return (left, top, right, bottom).
    If detection fails, return fallback area.
    """
    try:
        frame_rgba = frame.convert("RGBA")
        inv_bbox = get_transparent_bbox(frame_rgba)
        if inv_bbox:
            logger.info("Detected transparent screen bbox: %s", inv_bbox)
            return inv_bbox
    except Exception as e:
        logger.warning("Transparency detection failed: %s", e)

    # Fallback: return user-specified fallback rectangle or entire image minus small margin
    w, h = frame.size
    # Prefer fallback constants if frame roughly matches expected dimensions
    if w >= FALLBACK_SCREEN_W and h >= FALLBACK_SCREEN_H:
        left = FALLBACK_SCREEN_X
        top = FALLBACK_SCREEN_Y
        right = left + FALLBACK_SCREEN_W
        bottom = top + FALLBACK_SCREEN_H
        right = min(right, w)
        bottom = min(bottom, h)
        logger.info("Using fallback screen area (configured): %s", (left, top, right, bottom))
        return (left, top, right, bottom)

    # Otherwise use a centered rectangle with 90% area
    pad_x = int(w * 0.05)
    pad_y = int(h * 0.05)
    logger.info("Using centered fallback screen area (auto): %s", (pad_x, pad_y, w - pad_x, h - pad_y))
    return (pad_x, pad_y, w - pad_x, h - pad_y)


def _choose_text_color_for_region(image: Image.Image, bbox, light_color=(255, 255, 255), dark_color=(0, 0, 0)):
    """
    Choose text color (light or dark) based on average brightness inside bbox region.
    """
    left, top, right, bottom = bbox
    region = image.crop((left, top, right, bottom)).convert("L")
    stat = ImageStat.Stat(region)
    avg = stat.mean[0]
    # If region is dark (avg < 128) choose light color; else dark color
    return light_color if avg < 140 else dark_color


# -----------------------
# Image processing
# -----------------------
def generate_lockscreen(user_image_path: str) -> str:
    """
    Composite the user's wallpaper into the phone frame, draw date/time,
    and return output filepath.
    """
    # Load frame (RGBA)
    if not os.path.exists(FRAME_FILE):
        raise FileNotFoundError(f"Frame file not found: {FRAME_FILE}")

    frame = Image.open(FRAME_FILE).convert("RGBA")
    frame_w, frame_h = frame.size

    # Detect screen area
    left, top, right, bottom = get_screen_area(frame)
    screen_w = right - left
    screen_h = bottom - top

    # Load user wallpaper
    wallpaper = Image.open(user_image_path).convert("RGBA")
    wp_w, wp_h = wallpaper.size

    # Scale wallpaper to cover the screen (cover mode)
    scale = max(screen_w / wp_w, screen_h / wp_h)
    new_size = (int(wp_w * scale + 0.5), int(wp_h * scale + 0.5))
    wallpaper_resized = wallpaper.resize(new_size, Image.LANCZOS)

    # Center the wallpaper inside the detected screen area
    paste_x = left + (screen_w - new_size[0]) // 2
    paste_y = top + (screen_h - new_size[1]) // 2

    # Create canvas and paste wallpaper
    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 255))
    canvas.paste(wallpaper_resized, (paste_x, paste_y))

    # Choose text color based on wallpaper brightness in top area
    text_color = _choose_text_color_for_region(canvas, (left, top, right, top + int(screen_h * 0.18)))
    # Convert to tuple with alpha
    text_color_rgba = (text_color[0], text_color[1], text_color[2], 255)

    draw = ImageDraw.Draw(canvas)

    # Prepare date/time strings
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    date_text = now.strftime("%a, %B %d")  # Wed, December 3
    time_text = now.strftime("%I:%M").lstrip("0")  # 1:05 or 10:11

    # Load fonts (try large sizes; fallback if missing)
    font_date = safe_load_font(FONT_DATE, size=max(40, int(screen_w * 0.05)))
    font_time = safe_load_font(FONT_TIME, size=max(140, int(screen_w * 0.25)))

    # Positions: place near top of the screen area
    center_x = left + screen_w // 2
    date_y = top + int(screen_h * 0.05)  # small gap from top of screen
    time_y = top + int(screen_h * 0.16)  # below date

    # Draw shadow slightly for better contrast
    shadow_color = (0, 0, 0, 120) if text_color == (255, 255, 255) else (255, 255, 255, 160)
    try:
        # Many PIL builds support anchor argument "mm" for center alignment.
        draw.text((center_x + 2, date_y + 2), date_text, font=font_date, fill=shadow_color, anchor="mm")
        draw.text((center_x + 3, time_y + 3), time_text, font=font_time, fill=shadow_color, anchor="mm")
        draw.text((center_x, date_y), date_text, font=font_date, fill=text_color_rgba, anchor="mm")
        draw.text((center_x, time_y), time_text, font=font_time, fill=text_color_rgba, anchor="mm")
    except Exception:
        # If anchor isn't supported, fall back to manual measurement
        dd = draw.textsize(date_text, font=font_date)
        td = draw.textsize(time_text, font=font_time)
        draw.text((center_x - dd[0] / 2 + 2, date_y + 2), date_text, font=font_date, fill=shadow_color)
        draw.text((center_x - td[0] / 2 + 3, time_y + 3), time_text, font=font_time, fill=shadow_color)
        draw.text((center_x - dd[0] / 2, date_y), date_text, font=font_date, fill=text_color_rgba)
        draw.text((center_x - td[0] / 2, time_y), time_text, font=font_time, fill=text_color_rgba)

    # Finally paste the frame on top (use frame alpha as mask)
    canvas.paste(frame, (0, 0), frame)

    # Save output
    canvas.convert("RGB").save(OUTPUT_FILE, quality=92)
    logger.info("Saved output to %s", OUTPUT_FILE)
    return OUTPUT_FILE


# -----------------------
# Telegram handlers
# -----------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 Send me a wallpaper (photo or file) and I'll return an iPhone-style lockscreen mockup."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a photo (as image or file). I will generate lockscreen mockup.")


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles both photo messages and document images.
    Downloads the image to 'user_wallpaper.jpg', processes it and replies with the final picture.
    """
    msg = update.message
    try:
        await msg.reply_text("🖼️ Received. Processing... (this may take a couple seconds)")
        file_obj = None

        # Photo sent as compressed photo
        if msg.photo:
            file_obj = msg.photo[-1]
            new_file = await file_obj.get_file()
            input_path = "user_wallpaper.jpg"
            await new_file.download_to_drive(custom_path=input_path)
        # Or as a document (user uploaded original PNG/JPG)
        elif msg.document and msg.document.mime_type.startswith("image"):
            new_file = await context.bot.get_file(msg.document.file_id)
            input_path = "user_wallpaper.jpg"
            await new_file.download_to_drive(custom_path=input_path)
        else:
            await msg.reply_text("❌ Please send an image (photo or image file).")
            return

        logger.info("Downloaded user image to %s", input_path)
        output = generate_lockscreen(input_path)

        # Reply with final image
        await context.bot.send_photo(chat_id=msg.chat_id, photo=open(output, "rb"))
        logger.info("Sent final image to chat %s", msg.chat_id)

    except Exception as e:
        logger.exception("Error processing image:")
        await msg.reply_text(f"⚠️ Something went wrong while processing your image:\n{e}")


# -----------------------
# Main
# -----------------------
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Please set BOT_TOKEN in the script before running.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    # handle photos or documents that are images
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_image))

    logger.info("Bot started. Waiting for images...")
    app.run_polling()


if __name__ == "__main__":
    main()
