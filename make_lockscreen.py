import os
import traceback
import datetime
import pytz
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = "7764742692:AAHUJ8V1utjXASJNx4UClh8wQAaT4_EC-QY"
MOCKUP_FILE = "phone_frame.png"   # 372×750 mockup

# Pixel-perfect screen area
SCREEN_BBOX = (20, 92, 352, 735)

# Custom overrides
custom_time = None
custom_date = None

# ---------- IST TIME + DATE ----------

def get_time_text():
    global custom_time
    if custom_time:
        return custom_time
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.datetime.now(ist)
    return now.strftime("%-I:%M")  # Android style time

def get_date_text():
    global custom_date
    if custom_date:
        return custom_date
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.datetime.now(ist)
    return now.strftime("%a, %B %-d")  # Example: Mon, October 6

# ---------- COMMANDS ----------

def cmd_time(update, context):
    global custom_time
    try:
        custom_time = context.args[0]
        update.message.reply_text(f"✔ Time set to {custom_time}")
    except:
        update.message.reply_text("Usage: /time 10:11")

def cmd_date(update, context):
    global custom_date
    try:
        custom_date = " ".join(context.args)
        update.message.reply_text(f"✔ Date set to {custom_date}")
    except:
        update.message.reply_text("Usage: /date October 6")

def cmd_reset(update, context):
    global custom_time, custom_date
    custom_time = None
    custom_date = None
    update.message.reply_text("✔ Reset to real IST time & date.")

# ---------- IMAGE PROCESSING ----------

def process_image(wallpaper_path):
    frame = Image.open(MOCKUP_FILE).convert("RGBA")
    wallpaper = Image.open(wallpaper_path).convert("RGBA")

    left, top, right, bottom = SCREEN_BBOX
    screen_w = right - left
    screen_h = bottom - top

    wp_w, wp_h = wallpaper.size
    scale = max(screen_w / wp_w, screen_h / wp_h)
    new_size = (int(wp_w * scale), int(wp_h * scale))
    wallpaper_resized = wallpaper.resize(new_size, Image.LANCZOS)

    offset_x = left + (screen_w - new_size[0]) // 2
    offset_y = top + (screen_h - new_size[1]) // 2

    # Background black
    bg = Image.new("RGBA", frame.size, (0,0,0,255))
    result = bg.copy()

    result.paste(wallpaper_resized, (offset_x, offset_y), wallpaper_resized)
    result.alpha_composite(frame)

    draw = ImageDraw.Draw(result)

    # -------- ANDROID STYLE TEXT --------
    time_color = (0, 0, 0, 255)
    date_color = (0, 0, 0, 255)

    try:
        font_large = ImageFont.truetype("Roboto-Black.ttf", 150)   # VERY BOLD TIME
        font_small = ImageFont.truetype("Roboto-Medium.ttf", 45)   # Medium DATE
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    time_text = get_time_text()
    date_text = get_date_text()

    center_x = left + screen_w // 2

    # Perfect Android-style layout
    date_y = top + 40
    time_y = date_y + 70

    date_w = draw.textbbox((0,0), date_text, font=font_small)[2]
    time_w = draw.textbbox((0,0), time_text, font=font_large)[2]

    draw.text((center_x - date_w/2, date_y), date_text, font=font_small, fill=date_color)
    draw.text((center_x - time_w/2, time_y), time_text, font=font_large, fill=time_color)

    output = "final_output.jpg"
    result.convert("RGB").save(output, quality=95)
    return output

# ---------- BOT HANDLERS ----------

def start(update, context):
    update.message.reply_text("Send a picture and I'll create a clean Android lockscreen with real IST time 😎")

def handle_image(update, context):
    try:
        update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
        photo = update.message.photo[-1].get_file()
        photo_path = "user_wallpaper.jpg"
        photo.download(photo_path)

        final_image = process_image(photo_path)
        update.message.reply_photo(open(final_image, "rb"))
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")
        print(traceback.format_exc())

# ---------- MAIN ----------

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("time", cmd_time))
    dp.add_handler(CommandHandler("date", cmd_date))
    dp.add_handler(CommandHandler("reset", cmd_reset))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
