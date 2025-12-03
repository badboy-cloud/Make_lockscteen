import pytz
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ---- CONFIG ----
BOT_TOKEN = "7764742692:AAHUJ8V1utjXASJNx4UClh8wQAaT4_EC-QY"
FRAME_PATH = "phone_frame.png"        # transparent mockup PNG
FONT_DATE = "fonts/Roboto-Regular.ttf"
FONT_TIME = "fonts/Roboto-Black.ttf"

# Screen placement inside mockup
SCREEN_X = 85
SCREEN_Y = 130
SCREEN_W = 880
SCREEN_H = 1900


# ---- MAIN IMAGE PROCESSOR ----
def generate_lockscreen(wallpaper_path):
    # Load wallpaper
    wp = Image.open(wallpaper_path).convert("RGB")
    wp = wp.resize((SCREEN_W, SCREEN_H), Image.LANCZOS)

    # Load phone frame
    frame = Image.open(FRAME_PATH).convert("RGBA")

    # Canvas
    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 255))
    canvas.paste(wp, (SCREEN_X, SCREEN_Y))

    draw = ImageDraw.Draw(canvas)

    # Indian Time
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    date_text = now.strftime("%a, %B %d")
    time_text = now.strftime("%I:%M")

    # Load fonts
    font_date = ImageFont.truetype(FONT_DATE, 75)
    font_time = ImageFont.truetype(FONT_TIME, 240)

    center_x = frame.width // 2

    # Draw Date
    draw.text((center_x, SCREEN_Y + 70), date_text, fill="white",
              font=font_date, anchor="mm")

    # Draw Time
    draw.text((center_x, SCREEN_Y + 270), time_text,
              fill="white", font=font_time, anchor="mm")

    # Add frame on top
    canvas.paste(frame, (0, 0), frame)

    output = "final_output.jpg"
    canvas.convert("RGB").save(output, quality=95)
    return output


# ---- TELEGRAM HANDLERS ----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📱 Send me a wallpaper and I will turn it into an iPhone mockup!")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1].file_id
    file = await context.bot.get_file(photo)

    input_path = "user_wallpaper.jpg"
    await file.download_to_drive(input_path)

    final_img = generate_lockscreen(input_path)
    await update.message.reply_photo(photo=open(final_img, "rb"))


# ---- MAIN ----

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🔥 Lockscreen bot running on localhost...")
    application.run_polling()


if __name__ == "__main__":
    main()
