import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from PIL import Image, ImageDraw, ImageFont, ImageOps

BOT_TOKEN = "7764742692:AAHUJ8V1utjXASJNx4UClh8wQAaT4_EC-QY"
MOCKUP_FILE = "phone_frame.png"   # 1 mockup only

def detect_transparent_bbox(frame):
    if frame.mode != "RGBA":
        frame = frame.convert("RGBA")
    alpha = frame.split()[-1]
    inv = ImageOps.invert(alpha)
    return inv.getbbox()

def process_image(wallpaper_path):
    frame = Image.open(MOCKUP_FILE).convert("RGBA")
    wallpaper = Image.open(wallpaper_path).convert("RGBA")

    # Create black gradient background
    bg = Image.new("RGBA", frame.size, (0, 0, 0, 255))
    grad = Image.new("L", (1, frame.size[1]))

    for y in range(frame.size[1]):
        value = int(0 + (60 - 0) * (y / frame.size[1]))  # black → dark grey
        grad.putpixel((0, y), value)

    grad = grad.resize(frame.size)
    bg.putalpha(grad)
    result = bg.copy()

    # Insert wallpaper into phone screen
    bbox = detect_transparent_bbox(frame)
    left, top, right, bottom = bbox
    screen_w = right - left
    screen_h = bottom - top

    wp_w, wp_h = wallpaper.size
    scale = max(screen_w / wp_w, screen_h / wp_h)
    new_size = (int(wp_w * scale), int(wp_h * scale))

    wallpaper_resized = wallpaper.resize(new_size, Image.LANCZOS)
    offset_x = left + (screen_w - new_size[0]) // 2
    offset_y = top + (screen_h - new_size[1]) // 2

    result.paste(wallpaper_resized, (offset_x, offset_y), wallpaper_resized)
    result.alpha_composite(frame)

    # Add lockscreen text
    draw = ImageDraw.Draw(result)
    text_color = (220, 220, 220, 255)

    time_text = "10:11"
    date_text = "Mon, October 6"

    font_large = ImageFont.truetype("Roboto-Bold.ttf", size=140)
    font_small = ImageFont.truetype("Roboto-Regular.ttf", size=50)

    center_x = left + screen_w // 2
    time_y = top + 80
    date_y = top + 20

    time_w = draw.textbbox((0,0), time_text, font=font_large)[2]
    date_w = draw.textbbox((0,0), date_text, font=font_small)[2]

    draw.text((center_x - date_w/2, date_y), date_text, font=font_small, fill=text_color)
    draw.text((center_x - time_w/2, time_y), time_text, font=font_large, fill=text_color)

    # Save final output
    output = "final_output.jpg"
    result.convert("RGB").save(output, quality=95)

    return output

def start(update, context):
    update.message.reply_text("Send me a picture and I will make a lockscreen style image 😎")

def handle_image(update, context):
    update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)

    photo = update.message.photo[-1].get_file()
    photo_path = "user_wallpaper.jpg"
    photo.download(photo_path)

    final_image = process_image(photo_path)
    update.message.reply_photo(open(final_image, "rb"))

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()