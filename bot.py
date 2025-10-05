# -*- coding: utf-8 -*-

"""
Bot Telegram canggih untuk mengunduh media dengan yt-dlp.
Fitur:
- Pencarian interaktif dengan alur percakapan.
- Hasil pencarian visual dengan thumbnail dan tombol download inline.
- Pilihan format Video/Audio.
- Notifikasi status unduhan dan unggahan yang andal.
- Perintah /stop untuk mematikan bot secara aman (hanya pemilik).
- Penanganan file yang aman dan pembersihan otomatis.
"""

import logging
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler
)
from yt_dlp import YoutubeDL
from pinterest_dl import PinterestDL

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# State untuk ConversationHandler
GET_QUERY, GET_PINTEREST_QUERY = range(2)

# --- Handler Perintah Utama ---

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Hai {user.mention_html()}!\n\n"
        "Saya adalah bot pengunduh media. Kirim URL atau gunakan /search untuk mencari video.\n"
        "Gunakan /help untuk melihat semua perintah."
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Perintah yang tersedia:\n"
        "/start - Memulai bot\n"
        "/help - Menampilkan pesan ini\n"
        "/search - Memulai pencarian video interaktif\n"
        "/pinterest - Memulai pencarian gambar di Pinterest\n"
        "/stop - Menghentikan bot (hanya pemilik)\n\n"
        "Kirimkan URL video untuk diunduh."
    )

async def stop(update: Update, context: CallbackContext) -> None:
    OWNER_ID = os.getenv("OWNER_ID")
    if not OWNER_ID or str(update.effective_user.id) != OWNER_ID:
        await update.message.reply_text("Anda tidak diizinkan menggunakan perintah ini.")
        return

    await update.message.reply_text("Bot sedang dimatikan...")
    logger.info("Bot dihentikan oleh pemilik.")
    context.application.create_task(context.application.stop())


# --- Alur Percakapan untuk Pencarian ---

async def search_start(update: Update, context: CallbackContext) -> int:
    query = " ".join(context.args)
    if query:
        await perform_search(update.message, query, context)
        return ConversationHandler.END

    await update.message.reply_text("Apa yang ingin Anda cari?")
    return GET_QUERY

async def get_search_query(update: Update, context: CallbackContext) -> int:
    await perform_search(update.message, update.message.text, context)
    return ConversationHandler.END

async def perform_search(message, query: str, context: CallbackContext):
    status_msg = await message.reply_text(f"🔎 Mencari `{query}`...", parse_mode='Markdown')
    try:
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'default_search': 'ytsearch5',
            'quiet': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch5:{query}", download=False)

        await status_msg.delete()

        if 'entries' in result and result['entries']:
            await message.reply_text("Berikut adalah hasil pencarian teratas:")
            for entry in result['entries']:
                title = entry.get('title', 'N/A')
                video_url = entry.get('webpage_url', '')
                thumbnail_url = entry.get('thumbnail')
                duration = entry.get('duration_string', 'N/A')

                if not video_url: continue

                caption = f"<b>{title}</b>\n\nDurasi: {duration}"
                keyboard = [
                    [
                        InlineKeyboardButton("🎬 Unduh Video", callback_data=f"dl|video|{video_url}"),
                        InlineKeyboardButton("🎵 Unduh Audio", callback_data=f"dl|audio|{video_url}"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                try:
                    if thumbnail_url:
                        await context.bot.send_photo(
                            chat_id=message.chat_id, photo=thumbnail_url, caption=caption,
                            parse_mode='HTML', reply_markup=reply_markup
                        )
                    else: # Fallback jika tidak ada thumbnail
                        await context.bot.send_message(
                            chat_id=message.chat_id, text=caption, parse_mode='HTML', reply_markup=reply_markup
                        )
                except Exception as e:
                    logger.error(f"Gagal mengirim hasil pencarian: {e}. Mengirim sebagai teks.")
                    await context.bot.send_message(
                        chat_id=message.chat_id, text=caption, parse_mode='HTML', reply_markup=reply_markup
                    )
        else:
            await message.reply_text("Tidak ada hasil yang ditemukan.")
    except Exception as e:
        logger.error(f"Error saat mencari: {e}")
        await status_msg.edit_text("Terjadi kesalahan saat melakukan pencarian.")

async def cancel_search(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Pencarian dibatalkan.")
    return ConversationHandler.END


# --- Alur Percakapan untuk Pencarian Pinterest ---

async def pinterest_search_start(update: Update, context: CallbackContext) -> int:
    try:
        query = " ".join(context.args)
        if query:
            await perform_pinterest_search(update.message, query, context)
            return ConversationHandler.END

        await update.message.reply_text("Apa yang ingin Anda cari di Pinterest?")
        return GET_PINTEREST_QUERY
    except Exception as e:
        logger.error(f"Error in pinterest_search_start: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text(
                "Maaf, terjadi kesalahan saat memulai pencarian. Silakan coba lagi nanti."
            )
        return ConversationHandler.END

async def get_pinterest_query(update: Update, context: CallbackContext) -> int:
    await perform_pinterest_search(update.message, update.message.text, context)
    return ConversationHandler.END

async def perform_pinterest_search(message, query: str, context: CallbackContext):
    status_msg = await message.reply_text(f"🔎 Mencari `{query}` di Pinterest...", parse_mode='Markdown')
    try:
        # Jalankan panggilan sinkron yang memblokir di thread terpisah
        results = await asyncio.to_thread(PinterestDL.with_api().search, query=query, num=5)

        await status_msg.delete()

        if results:
            await message.reply_text("Berikut adalah hasil pencarian teratas di Pinterest:")
            for result in results:
                image_url = result.get('image_url')
                post_url = result.get('post_url')
                title = result.get('title', 'Tanpa Judul')

                if not image_url or not post_url:
                    continue

                caption = f"<b>{title}</b>"
                keyboard = [
                    [
                        InlineKeyboardButton("📌 Lihat Pin", url=post_url),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                try:
                    await context.bot.send_photo(
                        chat_id=message.chat_id, photo=image_url, caption=caption,
                        parse_mode='HTML', reply_markup=reply_markup
                    )
                except Exception as e:
                    logger.error(f"Gagal mengirim hasil Pinterest: {e}. URL: {image_url}")
                    # Fallback jika pengiriman foto gagal
                    await context.bot.send_message(
                        chat_id=message.chat_id, text=f"{caption}\n{post_url}",
                        parse_mode='HTML', reply_markup=reply_markup
                    )
        else:
            await message.reply_text("Tidak ada hasil yang ditemukan di Pinterest.")
    except Exception as e:
        logger.error(f"Error saat mencari di Pinterest: {e}", exc_info=True)
        await status_msg.edit_text("Terjadi kesalahan saat melakukan pencarian di Pinterest.")

async def cancel_pinterest_search(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Pencarian Pinterest dibatalkan.")
    return ConversationHandler.END


# --- Logika Unduhan ---

async def handle_url(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    if not (url.startswith('http://') or url.startswith('https://')):
        await update.message.reply_text("URL tidak valid. Untuk mencari, gunakan /search.")
        return

    keyboard = [[
        InlineKeyboardButton("🎬 Video", callback_data=f"dl|video|{url}"),
        InlineKeyboardButton("🎵 Audio", callback_data=f"dl|audio|{url}"),
    ]]
    await update.message.reply_text('Pilih format unduhan:', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    try:
        _, format_choice, url = query.data.split('|', 2)
    except ValueError:
        await query.edit_message_text("❌ Terjadi kesalahan: Data tidak valid.")
        return

    # Hapus tombol dari pesan asli untuk mencegah klik ganda
    if query.message.photo:
        await query.edit_message_reply_markup(reply_markup=None)
    else:
        await query.edit_message_text(f"Memproses: {query.message.text}", reply_markup=None)

    status_message = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"⏳ Memulai unduhan ({format_choice})..."
    )

    context.application.create_task(
        download_media(query.message.chat_id, context, url, format_choice, status_message)
    )

def progress_hook(d, status_message: Update.message, context: CallbackContext):
    if d['status'] == 'downloading':
        loop = asyncio.get_event_loop()
        if loop.is_running():
            percent = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()

            # Throttle updates to avoid hitting Telegram API limits
            now = loop.time()
            last_update = context.chat_data.get('last_update_time', 0)
            if now - last_update > 2:
                context.chat_data['last_update_time'] = now
                text = (f"📥 Mengunduh...\n\n"
                        f"**Progres:** {percent}\n"
                        f"**Kecepatan:** {speed}\n"
                        f"**ETA:** {eta}")
                asyncio.run_coroutine_threadsafe(
                    status_message.edit_text(text, parse_mode='Markdown'),
                    loop
                )

async def download_media(chat_id: int, context: CallbackContext, url: str, format_choice: str, status_message):
    filename = None
    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'noplaylist': True,
            'progress_hooks': [lambda d: progress_hook(d, status_message, context)],
            "nocheckcertificate": True,
        }
        if format_choice == 'video':
            ydl_opts['format'] = 'best[ext=mp4][height<=720]/best[ext=mp4]/best'
        else:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
            })

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            if format_choice == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'

        await status_message.edit_text(f"📤 Mengunggah `{os.path.basename(filename)}`...", parse_mode='Markdown')

        timeout_settings = {'read_timeout': 120, 'write_timeout': 120, 'connect_timeout': 120}
        with open(filename, 'rb') as f:
            if format_choice == 'video':
                await context.bot.send_video(
                    chat_id=chat_id, video=f, caption=info_dict.get('title'),
                    supports_streaming=True, **timeout_settings
                )
            else:
                await context.bot.send_audio(
                    chat_id=chat_id, audio=f, caption=info_dict.get('title'),
                    title=info_dict.get('title'), duration=info_dict.get('duration'), **timeout_settings
                )
        await status_message.delete()

    except Exception as e:
        logger.error(f"Error dalam download_media untuk URL {url}: {e}")
        error_message = str(e).split('ERROR: ')[-1]
        await status_message.edit_text(f"❌ Gagal memproses permintaan.\n\n**Alasan:**\n`{error_message}`", parse_mode='Markdown')
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
            logger.info(f"File sementara {os.path.basename(filename)} dihapus.")
        context.chat_data.pop('last_update_time', None)

def main() -> None:
    # Muat variabel dari file .env
    load_dotenv()

    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("Variabel environment TELEGRAM_TOKEN tidak diatur! Buat file .env atau ekspor variabel.")

    os.makedirs('downloads', exist_ok=True)

    application = Application.builder().token(TOKEN).build()

    search_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_start)],
        states={GET_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_search_query)]},
        fallbacks=[CommandHandler("cancel", cancel_search)],
    )

    pinterest_search_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("pinterest", pinterest_search_start)],
        states={GET_PINTEREST_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pinterest_query)]},
        fallbacks=[CommandHandler("cancel", cancel_pinterest_search)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(search_conv_handler)
    application.add_handler(pinterest_search_conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^dl\\|"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    logger.info("Bot siap digunakan...")
    application.run_polling()
    logger.info("Bot telah berhenti.")

if __name__ == '__main__':
    main()