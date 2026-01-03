# -*- coding: utf-8 -*-

"""
Bot Telegram Serbaguna
Fitur:
- /jadwal_azan <daerah>
- /cari_foto <query>
- /jadwal_konser
- /jadwal_live
"""

import logging
import os
from datetime import datetime
from typing import List
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv
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
GET_REGION, GET_PHOTO_QUERY = range(2)

# --- Impor untuk Playwright ---
from playwright.async_api import async_playwright

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
            "/cari_foto <query> - Mencari foto di Pinterest.\n"
            "/jadwal_konser - Menampilkan jadwal teater dan event JKT48.\n"
            "/jadwal_live - (Dalam Pengembangan) Info jadwal live streaming JKT48."
        )


# --- Logika untuk /jadwal_azan ---


async def jadwal_azan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Memulai alur untuk mendapatkan jadwal azan."""
    # Ambil daerah dari argumen jika ada
    region = " ".join(context.args) if getattr(context, "args", None) else ""

    if region:
        await fetch_and_send_prayer_times(update, context, region)
        return ConversationHandler.END

    # Jika tidak ada argumen, tanya pengguna
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

    # Tampilkan status awal menggunakan Markdown (safe)
    status_msg = await message.reply_text(
        f"⏳ Mencari jadwal sholat untuk `{region}`...", parse_mode=ParseMode.MARKDOWN
    )

    try:
        encoded_region = quote_plus(region.strip())
        # 1. Cari ID kota
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

        # 2. Dapatkan jadwal sholat berdasarkan ID kota
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


# --- Logika untuk /cari_foto ---


async def cari_foto_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Memulai alur untuk mencari foto di Pinterest."""
    query = " ".join(context.args) if getattr(context, "args", None) else ""
    if query:
        await fetch_and_send_pinterest_images(update, context, query)
        return ConversationHandler.END

    message = update.effective_message
    if message:
        await message.reply_text("Anda ingin mencari foto apa di Pinterest?")
    return GET_PHOTO_QUERY


async def get_photo_query_and_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mendapatkan query dari pengguna dan memulai pencarian."""
    query = update.effective_message.text if update.effective_message else ""
    await fetch_and_send_pinterest_images(update, context, query)
    return ConversationHandler.END


async def fetch_and_send_pinterest_images(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query: str
):
    """Mengambil dan mengirim gambar dari Pinterest menggunakan Playwright."""
    message = update.effective_message
    if not message:
        return

    status_msg = await message.reply_text(
        f"🔎 Mencari foto '{query}' di Pinterest...", parse_mode=ParseMode.MARKDOWN
    )

    image_urls: List[str] = []
    browser = None
    try:
        encoded_q = quote_plus(query.strip())
        search_url = f"https://www.pinterest.com/search/pins/?q={encoded_q}&rs=typed"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(search_url, timeout=15000)
            await page.wait_for_timeout(2500)  # Tunggu konten dimuat

            # Selector untuk menemukan gambar di halaman hasil pencarian
            locators = page.locator('div[data-test-id="pin-visual-wrapper"] img')
            count = await locators.count()

            if count == 0:
                await status_msg.edit_text("Tidak ada foto yang ditemukan.")
                return

            # Ambil maksimal 5 URL gambar
            for i in range(min(5, count)):
                img_locator = locators.nth(i)
                src = await img_locator.get_attribute("src")
                if src:
                    image_urls.append(src)

    except Exception:
        logger.exception("Error saat scraping Pinterest")
        await status_msg.edit_text("Terjadi kesalahan saat mencari foto di Pinterest.")
        return
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                logger.debug("Browser already closed or failed to close")

    if not image_urls:
        await status_msg.edit_text("Gagal mengekstrak URL gambar dari Pinterest.")
        return

    # Hapus pesan status sebelum mengirim gambar
    try:
        await status_msg.delete()
    except Exception:
        # tidak kritikal jika gagal menghapus
        pass

    # Kirim gambar: jika satu, gunakan send_photo, jika lebih gunakan send_media_group
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
    """Fungsi generik untuk scrape jadwal dari situs JKT48."""
    schedule_items: List[dict] = []
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=15000)

            # Cari semua entri jadwal
            entries = await page.locator(".entry-schedule__item").all()
            for entry in entries:
                title_element = entry.locator(".entry-schedule__item--title a")
                date_element = entry.locator(".entry-schedule__item--date")

                title = await title_element.inner_text()
                date_info = await date_element.inner_text()
                # Bersihkan dan format tanggal
                date = " ".join(date_info.split("\n"))

                schedule_items.append({"title": title.strip(), "date": date.strip()})

    except Exception:
        logger.exception("Gagal scrape jadwal JKT48")
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                logger.debug("Browser sudah tertutup atau gagal menutup")

    return schedule_items


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

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(jadwal_azan_conv_handler)
    application.add_handler(cari_foto_conv_handler)
    application.add_handler(CommandHandler("jadwal_konser", jadwal_jkt48))
    application.add_handler(CommandHandler("jadwal_live", jadwal_live))

    logger.info("Bot siap dijalankan...")
    application.run_polling()


if __name__ == "__main__":
    main()
