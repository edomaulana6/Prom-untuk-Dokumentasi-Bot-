# -*- coding: utf-8 -*-

"""
Bot Telegram Serbaguna
Fitur:
- /jadwal_azan <daerah>
- /cari_foto <query>  (menggunakan Bing Images, tanpa Playwright)
- /jadwal_konser
- /jadwal_live
"""

import logging
import os
import sys
import asyncio
import traceback
import html
from datetime import datetime
from typing import List
from urllib.parse import quote_plus
import json

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from youtubesearchpython.__future__ import VideosSearch
from telegram import InputMediaPhoto, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Konfigurasi logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States untuk ConversationHandlers
GET_REGION, GET_PHOTO_QUERY, GET_AUDIO_QUERY = range(3)

# --- Handler Perintah Utama ---


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan selamat datang."""
    message = update.effective_message
    if message:
        await message.reply_text(
            "Halo! Saya bot serbaguna. Gunakan /help untuk melihat perintah yang tersedia."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menampilkan daftar perintah."""
    message = update.effective_message
    if message:
        await message.reply_text(
            "Perintah yang tersedia:\n"
            "/jadwal_azan <daerah> - Mencari jadwal sholat.\n"
            "/cari_foto <query> - Mencari foto (menggunakan Bing Images).\n"
            "/cari_audio <query> - Mencari audio dari YouTube.\n"
            "/jadwal_konser - Menampilkan jadwal teater dan event JKT48.\n"
            "/jadwal_live - (Dalam Pengembangan) Info jadwal live streaming JKT48."
        )


# --- Logika untuk /jadwal_azan ---


async def jadwal_azan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Memulai alur untuk mendapatkan jadwal azan."""
    region = " ".join(context.args) if getattr(context, "args", None) else ""

    if region:
        await fetch_and_send_prayer_times(update, context, region)
        return ConversationHandler.END

    message = update.effective_message
    if message:
        await message.reply_text("Anda ingin mencari jadwal sholat untuk daerah mana?")
    return GET_REGION


async def get_region_and_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mendapatkan nama daerah dari pengguna dan mengambil data."""
    region = update.effective_message.text if update.effective_message else ""
    await fetch_and_send_prayer_times(update, context, region)
    return ConversationHandler.END


async def fetch_and_send_prayer_times(
    update: Update, context: ContextTypes.DEFAULT_TYPE, region: str
):
    """Mengambil dan mengirim jadwal sholat dari API."""
    message = update.effective_message
    if not message:
        return

    status_msg = await message.reply_text(
        f"⏳ Mencari jadwal sholat untuk `{region}`...", parse_mode=ParseMode.MARKDOWN
    )

    try:
        encoded_region = quote_plus(region.strip())
        async with httpx.AsyncClient(timeout=10.0) as client:
            search_url = f"https://api.myquran.com/v1/sholat/kota/cari/{encoded_region}"
            resp = await client.get(search_url)
            resp.raise_for_status()
            search_data = resp.json()

        if not search_data.get("status") or not search_data.get("data"):
            await status_msg.edit_text(f"❌ Daerah '{region}' tidak ditemukan.")
            return

        city_info = search_data["data"][0]
        city_id = city_info.get("id")
        city_name = city_info.get("lokasi", region)

        today = datetime.now()
        date_str = today.strftime("%Y/%m/%d")
        prayer_url = f"https://api.myquran.com/v1/sholat/jadwal/{city_id}/{date_str}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(prayer_url)
            resp.raise_for_status()
            prayer_data = resp.json()

        if not prayer_data.get("status") or not prayer_data.get("data"):
            await status_msg.edit_text("Gagal mendapatkan jadwal sholat.")
            return

        schedule = prayer_data["data"]["jadwal"]

        response_text = (
            f"<b>Jadwal Sholat untuk {city_name}</b>\n"
            f"Tanggal: {schedule.get('tanggal', date_str)}\n\n"
            f"Imsak: {schedule.get('imsak','-')}\n"
            f"Subuh: {schedule.get('subuh','-')}\n"
            f"Terbit: {schedule.get('terbit','-')}\n"
            f"Dhuha: {schedule.get('dhuha','-')}\n"
            f"Dzuhur: {schedule.get('dzuhur','-')}\n"
            f"Ashar: {schedule.get('ashar','-')}\n"
            f"Maghrib: {schedule.get('maghrib','-')}\n"
            f"Isya: {schedule.get('isya','-')}"
        )

        await status_msg.edit_text(response_text, parse_mode=ParseMode.HTML)

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error saat mengambil jadwal sholat: %s", e)
        await status_msg.edit_text(
            "Terjadi kesalahan saat berkomunikasi dengan server jadwal sholat."
        )
    except httpx.RequestError as e:
        logger.error("Request error saat mengambil jadwal sholat: %s", e)
        await status_msg.edit_text(
            "Terjadi kesalahan jaringan saat mengambil jadwal sholat."
        )
    except Exception:
        logger.exception("Error saat mengambil jadwal sholat")
        await status_msg.edit_text("Terjadi kesalahan yang tidak diketahui.")


# --- Logika untuk /cari_foto (menggunakan Bing Images, tanpa Playwright) ---


async def cari_foto_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Memulai alur untuk mencari foto."""
    query = " ".join(context.args) if getattr(context, "args", None) else ""
    if query:
        await fetch_and_send_pictures(update, context, query)
        return ConversationHandler.END

    message = update.effective_message
    if message:
        await message.reply_text("Anda ingin mencari foto apa?")
    return GET_PHOTO_QUERY


async def get_photo_query_and_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mendapatkan query dari pengguna dan memulai pencarian."""
    query = update.effective_message.text if update.effective_message else ""
    await fetch_and_send_pictures(update, context, query)
    return ConversationHandler.END


async def fetch_images_from_bing(query: str, limit: int = 5) -> List[str]:
    """
    Ambil URL gambar dari Bing Images hasil pencarian.
    Mengambil attribut 'm' pada elemen hasil (JSON) yang berisi field 'murl'.
    Tidak menggunakan Playwright.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }
    encoded_q = quote_plus(query)
    url = f"https://www.bing.com/images/search?q={encoded_q}&form=HDRSC2"

    image_urls: List[str] = []
    async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    # Elemen hasil gambar di Bing menyimpan metadata json di atribut 'm' pada tag <a class="iusc" ...>
    anchors = soup.select("a.iusc")
    for a in anchors:
        m = a.get("m")
        if not m:
            continue
        try:
            data = json.loads(m)
            murl = data.get("murl") or data.get("turl")
            if murl and murl not in image_urls:
                image_urls.append(murl)
                if len(image_urls) >= limit:
                    break
        except Exception:
            continue

    # Fallback: cari tag img langsung jika tidak cukup hasil
    if len(image_urls) < limit:
        for img in soup.select("img"):
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http") and src not in image_urls:
                image_urls.append(src)
                if len(image_urls) >= limit:
                    break

    return image_urls


async def fetch_and_send_pictures(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Mencari gambar dan mengirim ke chat (menggunakan Bing Images)."""
    message = update.effective_message
    if not message:
        return

    status_msg = await message.reply_text(f"🔎 Mencari foto '{query}'...", parse_mode=ParseMode.MARKDOWN)

    try:
        image_urls = await fetch_images_from_bing(query, limit=5)
    except httpx.RequestError:
        logger.exception("Gagal mengambil hasil pencarian gambar dari Bing")
        await status_msg.edit_text("Terjadi kesalahan jaringan saat mencari gambar.")
        return
    except Exception:
        logger.exception("Gagal mengambil gambar")
        await status_msg.edit_text("Terjadi kesalahan saat mencari gambar.")
        return

    if not image_urls:
        await status_msg.edit_text("Tidak ada foto yang ditemukan.")
        return

    # Hapus pesan status sebelum mengirim gambar (tidak krusial jika gagal)
    try:
        await status_msg.delete()
    except Exception:
        pass

    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    try:
        if len(image_urls) == 1:
            await context.bot.send_photo(chat_id=chat_id, photo=image_urls[0], caption=f"Hasil untuk: {query}")
        else:
            media_group = [
                InputMediaPhoto(media=url, caption=f"Hasil untuk: {query}" if i == 0 else "")
                for i, url in enumerate(image_urls)
            ]
            await context.bot.send_media_group(chat_id=chat_id, media=media_group)
    except Exception:
        logger.exception("Gagal mengirim gambar ke Telegram")
        await message.reply_text("Terjadi kesalahan saat mengirim gambar ke Telegram.")


# --- Logika untuk Jadwal JKT48 ---


async def jadwal_jkt48(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengambil dan mengirim jadwal konser dan event JKT48."""
    message = update.effective_message
    if not message:
        return

    status_msg = await message.reply_text("⏳ Mengambil jadwal terbaru JKT48...")

    try:
        theater_schedule = await scrape_jkt48_schedule(
            "https://jkt48.com/theater/schedule?lang=id"
        )
        event_schedule = await scrape_jkt48_schedule(
            "https://jkt48.com/event/schedule?lang=id"
        )

        if not theater_schedule and not event_schedule:
            await status_msg.edit_text("Tidak ada jadwal yang ditemukan saat ini.")
            return

        response_text = "<b>Jadwal JKT48 Terdekat</b>\n\n"

        if theater_schedule:
            response_text += "<b>-= Jadwal Teater =-</b>\n"
            for item in theater_schedule:
                response_text += f"- {item['title']} ({item['date']})\n"
            response_text += "\n"

        if event_schedule:
            response_text += "<b>-= Jadwal Event/Konser =-</b>\n"
            for item in event_schedule:
                response_text += f"- {item['title']} ({item['date']})\n"

        await status_msg.edit_text(response_text, parse_mode=ParseMode.HTML)

    except Exception:
        logger.exception("Error saat scraping jadwal JKT48")
        await status_msg.edit_text("Terjadi kesalahan saat mengambil jadwal JKT48.")


async def jadwal_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memberi tahu pengguna bahwa fitur jadwal live sedang dalam pengembangan."""
    message = update.effective_message
    if message:
        await message.reply_text(
            "Fitur untuk mengambil jadwal live streaming JKT48 dari Showroom saat ini sedang dalam pengembangan.\n\n"
            "Saya akan memberitahu Anda jika fitur ini sudah siap. Terima kasih atas pengertiannya!"
        )


async def scrape_jkt48_schedule(url: str) -> List[dict]:
    """Fungsi generik untuk scrape jadwal dari situs JKT48 (tanpa Playwright)."""
    schedule_items: List[dict] = []
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        entries = soup.select(".entry-schedule__item")
        for entry in entries:
            title_el = entry.select_one(".entry-schedule__item--title a")
            date_el = entry.select_one(".entry-schedule__item--date")
            if not title_el or not date_el:
                continue
            title = title_el.get_text(strip=True)
            date_info = date_el.get_text(" ", strip=True)
            schedule_items.append({"title": title, "date": date_info})

    except Exception:
        logger.exception("Gagal scrape jadwal JKT48")

    return schedule_items


# --- Logika untuk /cari_audio ---

async def cari_audio_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Memulai alur untuk mencari audio."""
    query = " ".join(context.args) if getattr(context, "args", None) else ""
    if query:
        await fetch_and_send_audio(update, context, query)
        return ConversationHandler.END

    message = update.effective_message
    if message:
        await message.reply_text("Anda ingin mencari audio apa?")
    return GET_AUDIO_QUERY


async def get_audio_query_and_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mendapatkan query audio dari pengguna dan memulai pencarian."""
    query = update.effective_message.text if update.effective_message else ""
    await fetch_and_send_audio(update, context, query)
    return ConversationHandler.END


async def fetch_and_send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Mencari audio di YouTube dan menampilkan 5 pilihan teratas."""
    message = update.effective_message
    if not message:
        return

    status_msg = await message.reply_text(f"🔎 Mencari 5 audio teratas untuk '{query}'...", parse_mode=ParseMode.MARKDOWN)

    # Langkah 1: Cari kandidat video
    videos_search = VideosSearch(query, limit=25)
    search_results = await videos_search.next()

    if not search_results or not search_results['result']:
        await status_msg.edit_text("Tidak ada video yang ditemukan.")
        return

    # Langkah 2: Filter untuk 5 video pertama yang valid
    valid_videos = []
    for video in search_results['result']:
        try:
            duration_parts = list(map(int, video.get('duration', '99:99').split(':')))
            if len(duration_parts) == 2:
                duration_seconds = duration_parts[0] * 60 + duration_parts[1]
            elif len(duration_parts) == 3:
                duration_seconds = duration_parts[0] * 3600 + duration_parts[1] * 60 + duration_parts[2]
            else:
                continue

            if 0 < duration_seconds < 600:
                video['duration_seconds'] = duration_seconds
                valid_videos.append(video)
                if len(valid_videos) >= 5:
                    break
        except (ValueError, TypeError):
            continue

    if not valid_videos:
        await status_msg.edit_text("Tidak ada audio yang ditemukan dengan durasi yang sesuai (di bawah 10 menit).")
        return

    # Langkah 3: Buat tombol inline untuk setiap video
    keyboard = []
    for video in valid_videos:
        title = video['title']
        duration = video['duration']
        callback_data = f"dl_audio:{video['id']}|{video['title']}|{video['duration_seconds']}"

        button_text = f"{title[:40]}... ({duration})" if len(title) > 40 else f"{title} ({duration})"

        if len(callback_data.encode('utf-8')) > 64:
            # Jika callback_data terlalu panjang, kita harus memotong judul di dalamnya juga
            truncated_title = video['title'][:20]
            callback_data = f"dl_audio:{video['id']}|{truncated_title}|{video['duration_seconds']}"

        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await status_msg.edit_text("Berikut adalah 5 hasil teratas. Silakan pilih satu untuk diunduh:", reply_markup=reply_markup)


async def audio_download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani callback dari tombol inline untuk mengunduh audio."""
    query = update.callback_query
    await query.answer()

    try:
        callback_data = query.data.split(':', 1)[1]
        video_id, video_title, duration_seconds_str = callback_data.split('|', 2)
        duration_seconds = int(duration_seconds_str)
    except (IndexError, ValueError):
        await query.edit_message_text("Callback tidak valid.")
        return

    await query.edit_message_text(f"✅ Pilihan diterima! Memulai proses unduh untuk '{video_title}'...")

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    output_path = f"/tmp/{video_id}.mp3"

    # Perintah unduh
    download_command = [
        sys.executable, '-m', 'yt_dlp',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--output', output_path,
        video_url,
    ]

    process = await asyncio.create_subprocess_exec(
        *download_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error("yt-dlp download error: %s", stderr.decode())
        await query.edit_message_text("Gagal mengunduh audio.")
        return

    if not os.path.exists(output_path):
        logger.error("File audio tidak ditemukan setelah diunduh: %s", output_path)
        await query.edit_message_text("Terjadi kesalahan setelah proses unduh.")
        return

    # Kirim audio
    await query.edit_message_text("🎧 Mengirim audio...")
    try:
        with open(output_path, 'rb') as audio_file:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_file,
                title=video_title,
                duration=duration_seconds,
                filename=f"{video_title}.mp3"
            )
        await query.delete_message()
    except Exception:
        logger.exception("Gagal mengirim file audio ke Telegram.")
        await query.edit_message_text("Gagal mengirim file audio.")
    finally:
        # Hapus file
        if os.path.exists(output_path):
            os.remove(output_path)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Membatalkan percakapan."""
    message = update.effective_message
    if message:
        await message.reply_text("Pencarian dibatalkan.")
    return ConversationHandler.END


# --- Error Handler ---

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangkap semua error dan mengirim notifikasi ke owner."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Memformat traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Mempersiapkan pesan notifikasi untuk owner
    update_str = update.to_json(indent=2) if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(update_str)}</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Mengirim notifikasi ke owner
    owner_id = os.getenv("OWNER_ID")
    if owner_id:
        await context.bot.send_message(
            chat_id=owner_id, text=message, parse_mode=ParseMode.HTML
        )

    # Memberi tahu pengguna (jika memungkinkan)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Maaf, terjadi kesalahan internal. Developer telah diberi tahu."
        )


def main() -> None:
    """Menjalankan bot."""
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN tidak diatur di .env")

    OWNER_ID = os.getenv("OWNER_ID")
    if not OWNER_ID:
        logger.warning("OWNER_ID tidak diatur di .env. Notifikasi error tidak akan dikirim.")

    application = Application.builder().token(TOKEN).build()

    # Mendaftarkan error handler
    application.add_error_handler(error_handler)

    # Conversation handler untuk /jadwal_azan
    jadwal_azan_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("jadwal_azan", jadwal_azan_start)],
        states={GET_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region_and_fetch)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Conversation handler untuk /cari_foto
    cari_foto_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("cari_foto", cari_foto_start)],
        states={GET_PHOTO_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_photo_query_and_fetch)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Conversation handler untuk /cari_audio
    cari_audio_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("cari_audio", cari_audio_start)],
        states={GET_AUDIO_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_audio_query_and_fetch)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Menambahkan handler untuk callback tombol audio
    application.add_handler(CallbackQueryHandler(audio_download_callback, pattern="^dl_audio:"))

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(jadwal_azan_conv_handler)
    application.add_handler(cari_foto_conv_handler)
    application.add_handler(cari_audio_conv_handler)
    application.add_handler(CommandHandler("jadwal_konser", jadwal_jkt48))
    application.add_handler(CommandHandler("jadwal_live", jadwal_live))

    logger.info("Bot siap dijalankan...")
    application.run_polling()


if __name__ == "__main__":
    main()
