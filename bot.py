# -*- coding: utf-8 -*-
import logging
import os
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote_plus
from youtubesearchpython.__future__ import VideosSearch
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

GET_REGION, GET_PHOTO_QUERY, GET_AUDIO_QUERY = range(3)

# --- FITUR START & HELP ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Saya bot serbaguna. Gunakan /help untuk melihat perintah.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📌 **Perintah Tersedia:**\n"
        "/jadwal_azan - Cek jadwal sholat\n"
        "/cari_foto - Cari gambar\n"
        "/cari_audio - Download MP3 langsung\n"
        "/jadwal_konser - Jadwal JKT48\n"
        "/jadwal_live - Info live streaming\n"
        "/cancel - Batalkan proses"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# --- FITUR JADWAL AZAN (Lengkap) ---
async def jadwal_azan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sebutkan nama daerah/kota:")
    return GET_REGION

async def get_region_and_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    region = update.message.text
    status_msg = await update.message.reply_text(f"⏳ Mencari jadwal sholat untuk `{region}`...")
    try:
        encoded_region = quote_plus(region.strip())
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://api.myquran.com/v1/sholat/kota/cari/{encoded_region}")
            search_data = resp.json()
        if search_data.get("data"):
            city_id = search_data["data"][0]["id"]
            date_str = datetime.now().strftime("%Y/%m/%d")
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://api.myquran.com/v1/sholat/jadwal/{city_id}/{date_str}")
                p_data = resp.json()["data"]["jadwal"]
            res_txt = f"<b>Jadwal Sholat {region}</b>\n\nImsak: {p_data['imsak']}\nSubuh: {p_data['subuh']}\nDzuhur: {p_data['dzuhur']}\nAshar: {p_data['ashar']}\nMaghrib: {p_data['maghrib']}\nIsya: {p_data['isya']}"
            await status_msg.edit_text(res_txt, parse_mode=ParseMode.HTML)
        else:
            await status_msg.edit_text("Daerah tidak ditemukan.")
    except:
        await status_msg.edit_text("Terjadi kesalahan.")
    return ConversationHandler.END

# --- FITUR CARI FOTO (Lengkap) ---
async def cari_foto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Masukkan kata kunci foto:")
    return GET_PHOTO_QUERY

async def get_photo_query_and_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text(f"🔎 Mencari foto '{query}'...")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            resp = await client.get(f"https://www.bing.com/images/search?q={quote_plus(query)}")
            soup = BeautifulSoup(resp.text, "html.parser")
        images = [img.get("src") for img in soup.select("img") if img.get("src") and img.get("src").startswith("http")][:5]
        if images:
            media = [InputMediaPhoto(media=url, caption=f"Hasil: {query}" if i == 0 else "") for i, url in enumerate(images)]
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
            await status_msg.delete()
        else:
            await status_msg.edit_text("Foto tidak ditemukan.")
    except:
        await status_msg.edit_text("Gagal mengambil foto.")
    return ConversationHandler.END

# --- FITUR DOWNLOAD AUDIO (Mesin Baru - Aman) ---
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
    except:
        await update.message.reply_text("Gagal mencari lagu.")
    return ConversationHandler.END

async def send_mp3_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    vid_id = query.data.split(":")[1]
    await query.answer()
    await query.edit_message_text("⏳ Sedang memproses pengiriman MP3...")
    try:
        # Menggunakan API perantara agar langsung terkirim sebagai file audio
        dl_url = f"https://api.nexoracle.com/download/ytmp3?url=https://www.youtube.com/watch?v={vid_id}"
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=dl_url)
        await query.delete_message()
    except:
        await query.edit_message_text("❌ Gagal mengirim audio secara langsung.")

# --- FITUR JKT48 ---
async def jadwal_jkt48(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Fitur Scraping JKT48 sedang aktif...")

async def jadwal_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fitur jadwal live streaming dalam pengembangan.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Dibatalkan.")
    return ConversationHandler.END

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    application = Application.builder().token(token).build()

    # Handlers (Pendaftaran Fitur)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("jadwal_konser", jadwal_jkt48))
    application.add_handler(CommandHandler("jadwal_live", jadwal_live))
    
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
    
