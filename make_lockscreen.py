import os
import pytz
from datetime import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from PIL import Image, ImageDraw, ImageFont


# ---------------------------
# CONFIG
# ---------------------------

BOT_TOKEN = "7764742692:AAHUJ8V1utjXASJNx4UClh8wQAaT4_EC-QY"

FRAME_PATH = "phone_frame.png"     # your transparent iPhone mockup
FONT_DATE = "fonts/SFPRODISPLAYREGULAR.OTF"
FONT_TIME = "fonts/SFPRODISPLAYBOLD.OTF"

# Screen placement (adjust perfectly for your PNG)
SCREEN_X = 85
SCREEN_Y = 130
SCREEN_W = 880
SCREEN_H = 1900


# ---------------------------
# PROCESS IMAGE FUNCTION
# ---------------------------

def generate_lockscreen(user_image_path):

    # Load user wallpaper
    wallpaper = Image.open(user_image_path).convert("RGB")
    wallpaper = wallpaper.resize((SCREEN_W, SCREEN_H), Image.LANCZOS)

    # Load frame
    frame = Image.open(FRAME_PATH).convert("RGBA")

    # Canvas
    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 255))

    # Paste wallpaper inside phone screen
    canvas.paste(wallpaper, (SCREEN_X, SCREEN_Y))

    draw = ImageDraw.Draw(canvas)

    # Get IST time
    india = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india)

    date_text = now.strftime("%a, %B %d")
    time_text = now.strftime("%I:%M")

    # Load fonts
    font_date = ImageFont.truetype(FONT_DATE, 75)    # date size
    font_time = ImageFont.truetype(FONT_TIME, 240)   # big time

    center_x = frame.width // 2

    # Draw date
    draw.text(
        (center_x, SCREEN_Y + 60),
        date_text,
        font=font_date,
        fill="white",
        anchor="mm"
    )

    # Draw time
    draw.text(
        (center_x, SCREEN_Y + 260),
        time_text,
        font=font_time,
        fill="white",
        anchor="mm"
    )

    # Add frame on top
    canvas.paste(frame, (0, 0), frame)

    output_path = "final_output.jpg"
    canvas.convert("RGB").save(output_path, quality=95)
    return output_path


# ---------------------------
# BOT HANDLERS
# ---------------------------

def start(update, context):
    update.message.reply_text(
        "Send me any picture and I will create a lockscreen mockup 😎"
    )


def handle_image(update, context):
    update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)

    try:
        file = update.message.photo[-1].get_file()
        input_path = "user_image.jpg"
        file.download(input_path)

        final_image = generate_lockscreen(input_path)

        update.message.reply_photo(open(final_image, "rb"))

    except Exception as e:
        update.message.reply_text("⚠️ Error processing image.")
        print("ERROR:", e)


# ---------------------------
# MAIN
# ---------------------------

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
