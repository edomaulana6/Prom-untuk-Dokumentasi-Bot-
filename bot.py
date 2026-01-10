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
from datetime import datetime
from typing import List
from urllib.parse import quote_plus
import json

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from youtubesearchpython.async import VideosSearch
from telegram import InputMediaPhoto, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
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
    """Mencari audio di YouTube dan mengirim hasilnya."""
    message = update.effective_message
    if not message:
        return

    status_msg = await message.reply_text(f"🔎 Mencari audio '{query}'...", parse_mode=ParseMode.MARKDOWN)

    try:
        # Langkah 1: Cari kandidat video menggunakan youtube-search-python
        videos_search = VideosSearch(query, limit=25)
        search_results = await videos_search.next()

        if not search_results or not search_results['result']:
            await status_msg.edit_text("Tidak ada video yang ditemukan.")
            return

        video_urls = [video['link'] for video in search_results['result']]

        # Langkah 2: Gunakan yt-dlp untuk memeriksa metadata dan memfilter durasi
        command = [
            sys.executable, '-m', 'yt_dlp',
            '--dump-json',
            '--no-playlist',
            '--match-filter', 'duration < 600',  # Filter durasi < 10 menit (600 detik)
            '--ignore-errors',
        ] + video_urls

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error("yt-dlp error: %s", stderr.decode())
            # Jangan langsung gagal, mungkin hanya beberapa URL yang error
            pass

        valid_videos = []
        for line in stdout.decode().strip().split('\n'):
            if line:
                try:
                    video_data = json.loads(line)
                    valid_videos.append(video_data)
                except json.JSONDecodeError:
                    continue

        if not valid_videos:
            await status_msg.edit_text("Tidak ada audio yang ditemukan dengan durasi yang sesuai.")
            return

        # Ambil 5 video teratas yang valid
        top_videos = valid_videos[:5]

        response_text = f"<b>Hasil Pencarian Audio untuk: {query}</b>\n\n"
        for i, video in enumerate(top_videos, 1):
            title = video.get('title', 'Tanpa Judul')
            duration_seconds = video.get('duration', 0)
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            duration_str = f"{minutes}:{seconds:02d}"
            url = video.get('webpage_url', '#')
            response_text += f"{i}. <a href='{url}'>{title}</a> ({duration_str})\n"

        await status_msg.edit_text(response_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except Exception as e:
        logger.exception("Error di fetch_and_send_audio: %s", e)
        await status_msg.edit_text("Terjadi kesalahan yang tidak diketahui saat mencari audio.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Membatalkan percakapan."""
    message = update.effective_message
    if message:
        await message.reply_text("Pencarian dibatalkan.")
    return ConversationHandler.END


def main() -> None:
    """Menjalankan bot."""
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN tidak diatur di .env")

    application = Application.builder().token(TOKEN).build()

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
