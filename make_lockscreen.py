import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime
import pytz

BOT_TOKEN = "7764742692:AAHUJ8V1utjXASJNx4UClh8wQAaT4_EC-QY"
MOCKUP_FILE = "phone_frame.png"   # <-- your fixed transparent mockup

# -------------------------------------------------------
# Detect transparent area inside the mockup (screen area)
# -------------------------------------------------------
def detect_transparent_bbox(frame):
    if frame.mode != "RGBA":
        frame = frame.convert("RGBA")
    alpha = frame.split()[-1]
    return alpha.getbbox()   # returns (left, top, right, bottom)

# -------------------------------------------------------
# IST date
# -------------------------------------------------------
def get_date_text():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    return now.strftime("%a, %B %-d")

# -------------------------------------------------------
# IST time
# -------------------------------------------------------
def get_time_text():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    return now.strftime("%-I:%M")   # 1:23 format (no leading zero)

# -------------------------------------------------------
# Compose final lockscreen image
# -------------------------------------------------------
def process_image(wallpaper_path):

    frame = Image.open(MOCKUP_FILE).convert("RGBA")
    wallpaper = Image.open(wallpaper_path).convert("RGBA")

    # Detect transparent screen area
    bbox = detect_transparent_bbox(frame)
    left, top, right, bottom = bbox
    screen_w = right - left
    screen_h = bottom - top

    # Resize wallpaper to fill the screen
    wp_w, wp_h = wallpaper.size
    scale = max(screen_w / wp_w, screen_h / wp_h)
    new_size = (int(wp_w * scale), int(wp_h * scale))
    wallpaper_resized = wallpaper.resize(new_size, Image.LANCZOS)

    # Center inside transparent screen
    offset_x = left + (screen_w - new_size[0]) // 2
    offset_y = top + (screen_h - new_size[1]) // 2

    result = Image.new("RGBA", frame.size)
    result.paste(wallpaper_resized, (offset_x, offset_y), wallpaper_resized)
    result.alpha_composite(frame)

    draw = ImageDraw.Draw(result)

    # -------------------------------------------------------
    # Text settings (BIG TIME)
    # -------------------------------------------------------
    time_text = get_time_text()
    date_text = get_date_text()

    time_color = (0, 0, 0, 255)
    date_color = (0, 0, 0, 255)

    try:
        font_large = ImageFont.truetype("Roboto-Black.ttf", 200)  
        font_small = ImageFont.truetype("Roboto-Medium.ttf", 60)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Centering X
    center_x = left + screen_w // 2

    # Position Y (tuned for iPhone mockup)
    date_y = top + 90
    time_y = date_y + 120

    # Center text
    date_w = draw.textbbox((0,0), date_text, font=font_small)[2]
    time_w = draw.textbbox((0,0), time_text, font=font_large)[2]

    draw.text((center_x - date_w/2, date_y), date_text, font=font_small, fill=date_color)
    draw.text((center_x - time_w/2, time_y), time_text, font=font_large, fill=time_color)

    # Save final output
    output = "final_output.jpg"
    result.convert("RGB").save(output, quality=95)
    return output

# -------------------------------------------------------
# Telegram Bot Handlers
# -------------------------------------------------------
def start(update, context):
    update.message.reply_text(
        "Send me any picture and I will create a lockscreen mockup 😎"
    )

def handle_image(update, context):
    update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)

    photo = update.message.photo[-1].get_file()
    photo_path = "user_wallpaper.jpg"
    photo.download(photo_path)

    final_image = process_image(photo_path)
    update.message.reply_photo(open(final_image, "rb"))

# -------------------------------------------------------
# Run Bot
# -------------------------------------------------------
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
