# -*- coding: utf-8 -*-
import logging
import os
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from youtubesearchpython.__future__ import VideosSearch
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

load_dotenv()

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# States
GET_REGION, GET_PHOTO_QUERY, GET_AUDIO_QUERY = range(3)

# --- FITUR START & HELP (TETAP) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Aktif! Gunakan /help untuk melihat perintah.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📌 **Perintah Tersedia:**\n"
        "/jadwal_azan - Cek jadwal sholat\n"
        "/cari_foto - Cari gambar\n"
        "/cari_audio - Download MP3 langsung\n"
        "/jadwal_konser - Jadwal JKT48\n"
        "/cancel - Batalkan proses"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# --- FITUR JADWAL AZAN (TETAP) ---
async def jadwal_azan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sebutkan nama daerah/kota:")
    return GET_REGION

async def get_region_and_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    region = update.message.text
    # Logika API MyQuran Anda tetap di sini...
    await update.message.reply_text(f"Mencari jadwal azan untuk {region}...")
    return ConversationHandler.END

# --- FITUR CARI FOTO (TETAP) ---
async def cari_foto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Masukkan kata kunci foto:")
    return GET_PHOTO_QUERY

async def get_photo_query_and_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    # Logika Scraping Bing tetap di sini...
    await update.message.reply_text(f"Mencari foto: {query}...")
    return ConversationHandler.END

# --- FITUR DOWNLOAD AUDIO (REVISI AMAN) ---
async def cari_audio_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Masukkan judul lagu:")
    return GET_AUDIO_QUERY

async def get_audio_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    try:
        videos_search = VideosSearch(query, limit=1)
        results = await videos_search.next()
        if results['result']:
            vid = results['result'][0]
            keyboard = [[InlineKeyboardButton("📩 KIRIM MP3 LANGSUNG", callback_data=f"send_mp3:{vid['id']}")]]
            await update.message.reply_text(
                f"✅ **Ditemukan:** {vid['title']}\nKlik tombol untuk mengirim file:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await update.message.reply_text("Gagal mencari lagu.")
    return ConversationHandler.END

async def send_mp3_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    vid_id = query.data.split(":")[1]
    await query.answer()
    await query.edit_message_text("⏳ Sedang mengirim file MP3... mohon tunggu.")
    try:
        # Link API Perantara agar tidak kena blokir YouTube
        dl_url = f"https://api.nexoracle.com/download/ytmp3?url=https://www.youtube.com/watch?v={vid_id}"
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=dl_url)
    except:
        await query.edit_message_text("❌ Gagal mengirim audio.")

# --- FITUR JKT48 (TETAP) ---
async def jadwal_jkt48(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Mengecek jadwal konser JKT48...")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Dibatalkan.")
    return ConversationHandler.END

# --- MAIN ENGINE ---
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    application = Application.builder().token(token).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("jadwal_konser", jadwal_jkt48))
    
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("jadwal_azan", jadwal_azan_start)],
        states={GET_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region_and_fetch)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("cari_foto", cari_foto_start)],
        states={GET_PHOTO_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_photo_query_and_fetch)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("cari_audio", cari_audio_start)],
        states={GET_AUDIO_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_audio_results)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    application.add_handler(CallbackQueryHandler(send_mp3_callback, pattern="^send_mp3:"))

    application.run_polling()

if __name__ == "__main__":
    main()
                            
