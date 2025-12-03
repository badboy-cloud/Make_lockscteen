import os
import traceback
import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = "7764742692:AAHUJ8V1utjXASJNx4UClh8wQAaT4_EC-QY"
MOCKUP_FILE = "phone_frame.png"   # 372×750 transparent mockup

# Pixel-perfect screen box
SCREEN_BBOX = (20, 92, 352, 735)

# User overrides (optional)
custom_time = None
custom_date = None

def get_time_text():
    global custom_time
    if custom_time:
        return custom_time
    return datetime.datetime.now().strftime("%-I:%M")

def get_date_text():
    global custom_date
    if custom_date:
        return custom_date
    return datetime.datetime.now().strftime("%a, %B %-d")

def cmd_time(update, context):
    global custom_time
    try:
        custom_time = context.args[0]
        update.message.reply_text(f"✔ Custom time set to: {custom_time}")
    except:
        update.message.reply_text("Usage: /time 10:11")

def cmd_date(update, context):
    global custom_date
    try:
        custom_date = " ".join(context.args)
        update.message.reply_text(f"✔ Custom date set to: {custom_date}")
    except:
        update.message.reply_text("Usage: /date October 6")

def cmd_reset(update, context):
    global custom_time, custom_date
    custom_time = None
    custom_date = None
    update.message.reply_text("✔ Time & Date reset to REAL LIVE values.")

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

    bg = Image.new("RGBA", frame.size, (0, 0, 0, 255))
    result = bg.copy()

    result.paste(wallpaper_resized, (offset_x, offset_y), wallpaper_resized)
    result.alpha_composite(frame)

    draw = ImageDraw.Draw(result)
    text_color = (255, 255, 255, 255)

    time_text = get_time_text()
    date_text = get_date_text()

    try:
        font_large = ImageFont.truetype("Roboto-Bold.ttf", 60)
        font_small = ImageFont.truetype("Roboto-Regular.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    center_x = left + screen_w // 2
    time_y = top + 30
    date_y = top + 5

    time_w = draw.textbbox((0,0), time_text, font=font_large)[2]
    date_w = draw.textbbox((0,0), date_text, font=font_small)[2]

    draw.text((center_x - date_w/2, date_y), date_text, font=font_small, fill=text_color)
    draw.text((center_x - time_w/2, time_y), time_text, font=font_large, fill=text_color)

    output = "final_output.jpg"
    result.convert("RGB").save(output, quality=95)
    return output

def start(update, context):
    update.message.reply_text("Send me a picture and I'll create a perfect iPhone lockscreen with LIVE time 😎")

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
