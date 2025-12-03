import os
import traceback
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = "7764742692:AAHUJ8V1utjXASJNx4UClh8wQAaT4_EC-QY"
MOCKUP_FILE = "phone_frame.png"   # 372×750 mockup from webmobilefirst

# *** Pixel-perfect screen region for 372×750 mockup ***
SCREEN_BBOX = (23, 116, 350, 737)   # (left, top, right, bottom)

def process_image(wallpaper_path):
    frame = Image.open(MOCKUP_FILE).convert("RGBA")
    wallpaper = Image.open(wallpaper_path).convert("RGBA")

    # Use manual bounding box
    left, top, right, bottom = SCREEN_BBOX
    screen_w = right - left
    screen_h = bottom - top

    # Resize wallpaper to fill screen
    wp_w, wp_h = wallpaper.size
    scale = max(screen_w / wp_w, screen_h / wp_h)
    new_size = (int(wp_w * scale), int(wp_h * scale))

    wallpaper_resized = wallpaper.resize(new_size, Image.LANCZOS)

    # Center resized wallpaper inside screen area
    offset_x = left + (screen_w - new_size[0]) // 2
    offset_y = top + (screen_h - new_size[1]) // 2

    # Black gradient background
    bg = Image.new("RGBA", frame.size, (0,0,0,255))
    grad = Image.new("L", (1, frame.size[1]))
    for y in range(frame.size[1]):
        grad.putpixel((0, y), int(0 + (60 - 0) * (y / frame.size[1])))
    grad = grad.resize(frame.size)
    bg.putalpha(grad)
    result = bg.copy()

    # Insert wallpaper into screen
    result.paste(wallpaper_resized, (offset_x, offset_y), wallpaper_resized)

    # Put phone frame on top
    result.alpha_composite(frame)

    # Add time & date text
    draw = ImageDraw.Draw(result)
    text_color = (255,255,255,255)

    time_text = "10:11"
    date_text = "Mon, October 6"

    try:
        font_large = ImageFont.truetype("Roboto-Bold.ttf", 50)
        font_small = ImageFont.truetype("Roboto-Regular.ttf", 22)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Position text inside screen
    center_x = left + screen_w // 2
    time_y = top + 25
    date_y = top + 5

    # Center align
    time_w = draw.textbbox((0,0), time_text, font=font_large)[2]
    date_w = draw.textbbox((0,0), date_text, font=font_small)[2]

    draw.text((center_x - date_w/2, date_y), date_text, font=font_small, fill=text_color)
    draw.text((center_x - time_w/2, time_y), time_text, font=font_large, fill=text_color)

    # Save final image
    output = "final_output.jpg"
    result.convert("RGB").save(output, quality=95)
    return output

def start(update, context):
    update.message.reply_text("Send a picture and I will create a perfect iPhone lockscreen mockup 😎")

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
    dp.add_handler(MessageHandler(Filters.photo, handle_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
