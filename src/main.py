import os
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import time
import random
from time import sleep

BOT_TOKEN = "7738588776:AAG7ozt-0WipdnZQM8BDIxTwUWnNQ1kOeSA"

# At the top of the file, add a BASE_DIR constant
BASE_DIR = Path(__file__).resolve().parent.parent
FFMPEG_PATH = BASE_DIR / 'ffmpeg-7.1.1-essentials_build/bin'
DOWNLOAD_DIR = BASE_DIR / 'downloads'
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Logging
import logging
logging.basicConfig(level=logging.INFO)

# Add these constants
MAX_RETRIES = 3
RETRY_DELAY = 5

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎶 Send me the name of a song and I’ll show you the top 10 YouTube results to download!")

async def get_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    print(f"🔹 Received message: {query}")

    if query.isdigit():
        await update.message.reply_text("❌ Please send a song name, not a number.")
        return

    # Acknowledge the request immediately
    await update.message.reply_text(f"🔎 Searching YouTube for: {query}...")

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'ffmpeg_location': str(FFMPEG_PATH),  # Use the defined FFMPEG_PATH
        'format': 'bestaudio/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'extract_flat': True,  # Fetch only metadata without downloading
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'ignoreerrors': True,
        'no_warnings': True,
    }

    for attempt in range(MAX_RETRIES):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{query}", download=False)
                results = info.get('entries', [])

            # Debug: Log raw results
            print(f"🔍 Raw results: {results}")

            # Filter out results without a valid 'url'
            filtered_results = [result for result in results if 'url' in result]

            if filtered_results:
                context.user_data['search_results'] = filtered_results

                keyboard = [
                    [InlineKeyboardButton(f"{i+1}. {result['title']}", callback_data=str(i))]
                    for i, result in enumerate(filtered_results)
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("🎧 Choose a song to download:", reply_markup=reply_markup)
                return

            # If we get here, no results were found in this attempt
            sleep_time = RETRY_DELAY * (attempt + 1)
            print(f"⚠️ Attempt {attempt + 1} failed, waiting {sleep_time} seconds...")
            await asyncio.sleep(sleep_time)

        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed with error: {str(e)}")
            if "429" in str(e):  # Rate limit error
                sleep_time = RETRY_DELAY * (attempt + 1) + random.uniform(1, 5)
                print(f"🕒 Rate limited, waiting {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)
            else:
                break

    # If we get here, all attempts failed
    await update.message.reply_text("❌ Unable to fetch results. Please try again later.")

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = int(update.callback_query.data)
    results = context.user_data.get('search_results', [])

    if not (0 <= index < len(results)):
        await update.callback_query.answer("❌ Invalid selection.")
        return

    track = results[index]
    title = track.get('title', 'Unknown Title')
    url = track.get('url')  # Use 'url' instead of 'webpage_url'

    if not url:
        await update.callback_query.answer("❌ Unable to download this track.")
        await update.callback_query.message.reply_text("⚠️ This track does not have a valid download URL.")
        return

    await update.callback_query.answer(f"🎵 Downloading: {title}...")

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'ffmpeg_location': str(FFMPEG_PATH),  # Use the defined FFMPEG_PATH
        'format': 'bestaudio/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'ignoreerrors': True,
        'no_warnings': True,
    }

    for attempt in range(MAX_RETRIES):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                raw_file = ydl.prepare_filename(info)
                mp3_file = Path(raw_file).with_suffix('.mp3')
                print(f"✅ Downloaded file path: {mp3_file}")

            if mp3_file.exists():
                with mp3_file.open('rb') as f:
                    await update.callback_query.message.reply_audio(audio=f, title=title)
                    print("📤 File sent successfully.")
                mp3_file.unlink(missing_ok=True)
                return

            sleep_time = RETRY_DELAY * (attempt + 1)
            await asyncio.sleep(sleep_time)

        except Exception as e:
            print(f"⚠️ Download attempt {attempt + 1} failed: {str(e)}")
            if "429" in str(e):
                sleep_time = RETRY_DELAY * (attempt + 1) + random.uniform(1, 5)
                await asyncio.sleep(sleep_time)
            else:
                break

    await update.callback_query.message.reply_text("❌ Download failed. Please try again later.")

    time.sleep(5)  # Add a 5-second delay between requests

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_music))
    app.add_handler(CallbackQueryHandler(download_and_send))

    print("🤖 Bot is running...")
    app.run_polling()
