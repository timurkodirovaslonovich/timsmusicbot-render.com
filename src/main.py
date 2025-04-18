# filepath: tims-bot/src/main.py
import os
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
from dotenv import load_dotenv
import requests

# Load the .env file from the base directory
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

BOT_TOKEN = os.getenv("BOT_TOKEN")
FFMPEG_PATH = os.getenv("FFMPEG_PATH")

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

import logging
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎶 Send me the name of a song and I’ll show you the top 10 YouTube results to download!")

async def get_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    print(f"🔹 Received message: {query}")

    if query.isdigit():
        await update.message.reply_text("❌ Please send a song name, not a number.")
        return

    await update.message.reply_text(f"🔎 Searching YouTube for: {query}...")

    API_KEY = "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"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={API_KEY}&type=video"
    response = requests.get(url)
    results = response.json()
    print(results)

    ydl_opts = {
    'quiet': True,
    'noplaylist': True,
    'ffmpeg_location': FFMPEG_PATH,
    'format': 'bestaudio/best',
    'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
    'extract_flat': True,
    'cookiesfrombrowser': ('chrome',),  # Replace 'chrome' with your browser (e.g., 'firefox', 'edge')
    'geo_bypass': True,
    'geo_bypass_country': 'UZ',
}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            results = info.get('entries', [])

        print(f"🔍 Raw results: {results}")

        filtered_results = [result for result in results if 'url' in result]

        if not filtered_results:
            await update.message.reply_text("❌ No valid results found. Please try a different query.")
            return

        context.user_data['search_results'] = filtered_results

        keyboard = [
            [InlineKeyboardButton(f"{i+1}. {result['title']}", callback_data=str(i))]
            for i, result in enumerate(filtered_results)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🎧 Choose a song to download:", reply_markup=reply_markup)

    except Exception as e:
        print(f"⚠️ Exception: {e}")
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = int(update.callback_query.data)
    results = context.user_data.get('search_results', [])

    if not (0 <= index < len(results)):
        await update.callback_query.answer("❌ Invalid selection.")
        return

    track = results[index]
    title = track.get('title', 'Unknown Title')
    url = track.get('url')

    if not url:
        await update.callback_query.answer("❌ Unable to download this track.")
        await update.callback_query.message.reply_text("⚠️ This track does not have a valid download URL.")
        return

    await update.callback_query.answer(f"🎵 Downloading: {title}...")

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'ffmpeg_location': FFMPEG_PATH,
        'format': 'bestaudio/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_file = ydl.prepare_filename(info)
            mp3_file = Path(raw_file).with_suffix('.mp3')
            print(f"✅ Downloaded file path: {mp3_file}")

        if not mp3_file.exists():
            print("❌ File not found after download.")
            await update.callback_query.message.reply_text("❌ File not found.")
            return

        with mp3_file.open('rb') as f:
            await update.callback_query.message.reply_audio(audio=f, title=title)
            print("📤 File sent successfully.")

        mp3_file.unlink(missing_ok=True)

    except Exception as e:
        print(f"⚠️ Exception: {e}")
        await update.callback_query.message.reply_text(f"⚠️ Error: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_music))
    app.add_handler(CallbackQueryHandler(download_and_send))

    print("🤖 Bot is running...")
    app.run_polling()