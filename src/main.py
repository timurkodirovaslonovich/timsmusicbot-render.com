import os
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

BOT_TOKEN = "7738588776:AAG7ozt-0WipdnZQM8BDIxTwUWnNQ1kOeSA"




# Use pathlib for cross-platform paths
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)




# Logging
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

    # Acknowledge the request immediately
    await update.message.reply_text(f"🔎 Searching YouTube for: {query}...")

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'ffmpeg_location': 'C:/ffmpeg/bin',  # Adjust this path
        'format': 'bestaudio/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'extract_flat': True,  # Fetch only metadata without downloading
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            results = info.get('entries', [])

        # Debug: Log raw results
        print(f"🔍 Raw results: {results}")

        # Filter out results without a valid 'url'
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
    url = track.get('url')  # Use 'url' instead of 'webpage_url'

    if not url:
        await update.callback_query.answer("❌ Unable to download this track.")
        await update.callback_query.message.reply_text("⚠️ This track does not have a valid download URL.")
        return

    await update.callback_query.answer(f"🎵 Downloading: {title}...")

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'ffmpeg_location': 'C:/ffmpeg-7.1.1-essentials_build/bin',  # Confirm ffmpeg path
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
