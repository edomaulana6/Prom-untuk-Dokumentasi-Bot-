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
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States untuk ConversationHandlers
GET_REGION, GET_PHOTO_QUERY = range(2)

# --- Impor untuk Playwright ---
from playwright.async_api import async_playwright
import asyncio

# --- Handler Perintah Utama ---

async def start(update: Update, context: CallbackContext) -> None:
    """Mengirim pesan selamat datang."""
    await update.message.reply_text(
        "Halo! Saya bot serbaguna. Gunakan /help untuk melihat perintah yang tersedia."
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    """Menampilkan daftar perintah."""
    await update.message.reply_text(
        "Perintah yang tersedia:\n"
        "/jadwal_azan <daerah> - Mencari jadwal sholat.\n"
        "/cari_foto <query> - Mencari foto di Pinterest.\n"
        "/jadwal_konser - Menampilkan jadwal teater dan event JKT48.\n"
        "/jadwal_live - (Dalam Pengembangan) Info jadwal live streaming JKT48."
    )

# --- Logika untuk /jadwal_azan ---

async def jadwal_azan_start(update: Update, context: CallbackContext) -> int:
    """Memulai alur untuk mendapatkan jadwal azan."""
    # Ambil daerah dari argumen jika ada
    region = " ".join(context.args)

    if region:
        await fetch_and_send_prayer_times(update, context, region)
        return ConversationHandler.END

    # Jika tidak ada argumen, tanya pengguna
    await update.message.reply_text("Anda ingin mencari jadwal sholat untuk daerah mana?")
    return GET_REGION

async def get_region_and_fetch(update: Update, context: CallbackContext) -> int:
    """Mendapatkan nama daerah dari pengguna dan mengambil data."""
    region = update.message.text
    await fetch_and_send_prayer_times(update, context, region)
    return ConversationHandler.END

async def fetch_and_send_prayer_times(update: Update, context: CallbackContext, region: str):
    """Mengambil dan mengirim jadwal sholat dari API."""
    message = await update.message.reply_text(f"⏳ Mencari jadwal sholat untuk `{region}`...", parse_mode='Markdown')

    try:
        # 1. Cari ID kota
        async with httpx.AsyncClient() as client:
            search_url = f"https://api.myquran.com/v1/sholat/kota/cari/{region}"
            response = await client.get(search_url)
            response.raise_for_status()
            search_data = response.json()

        if not search_data.get('status') or not search_data.get('data'):
            await message.edit_text(f"❌ Daerah '{region}' tidak ditemukan.")
            return

        city_id = search_data['data'][0]['id']
        city_name = search_data['data'][0]['lokasi']

        # 2. Dapatkan jadwal sholat berdasarkan ID kota
        # (API ini tampaknya lebih baik dan aktif)
        from datetime import datetime
        today = datetime.now()
        date_str = today.strftime("%Y/%m/%d")

        prayer_url = f"https://api.myquran.com/v1/sholat/jadwal/{city_id}/{date_str}"
        async with httpx.AsyncClient() as client:
            response = await client.get(prayer_url)
            response.raise_for_status()
            prayer_data = response.json()

        if not prayer_data.get('status') or not prayer_data.get('data'):
            await message.edit_text("Gagal mendapatkan jadwal sholat.")
            return

        schedule = prayer_data['data']['jadwal']

        response_text = (
            f"<b>Jadwal Sholat untuk {city_name}</b>\n"
            f"Tanggal: {schedule['tanggal']}\n\n"
            f"Imsak: {schedule['imsak']}\n"
            f"Subuh: {schedule['subuh']}\n"
            f"Terbit: {schedule['terbit']}\n"
            f"Dhuha: {schedule['dhuha']}\n"
            f"Dzuhur: {schedule['dzuhur']}\n"
            f"Ashar: {schedule['ashar']}\n"
            f"Maghrib: {schedule['maghrib']}\n"
            f"Isya: {schedule['isya']}"
        )

        await message.edit_text(response_text, parse_mode='HTML')

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error saat mengambil jadwal sholat: {e}")
        await message.edit_text("Terjadi kesalahan saat berkomunikasi dengan server jadwal sholat.")
    except Exception as e:
        logger.error(f"Error saat mengambil jadwal sholat: {e}")
        await message.edit_text("Terjadi kesalahan yang tidak diketahui.")

# --- Logika untuk /cari_foto ---

async def cari_foto_start(update: Update, context: CallbackContext) -> int:
    """Memulai alur untuk mencari foto di Pinterest."""
    query = " ".join(context.args)
    if query:
        await fetch_and_send_pinterest_images(update, context, query)
        return ConversationHandler.END

    await update.message.reply_text("Anda ingin mencari foto apa di Pinterest?")
    return GET_PHOTO_QUERY

async def get_photo_query_and_fetch(update: Update, context: CallbackContext) -> int:
    """Mendapatkan query dari pengguna dan memulai pencarian."""
    query = update.message.text
    await fetch_and_send_pinterest_images(update, context, query)
    return ConversationHandler.END

async def fetch_and_send_pinterest_images(update: Update, context: CallbackContext, query: str):
    """Mengambil dan mengirim gambar dari Pinterest menggunakan Playwright."""
    message = await update.message.reply_text(f"🔎 Mencari foto '{query}' di Pinterest...", parse_mode='Markdown')

    image_urls = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            search_url = f"https://www.pinterest.com/search/pins/?q={query}&rs=typed"
            await page.goto(search_url)
            await page.wait_for_timeout(3000) # Tunggu konten dimuat

            # Selector untuk menemukan gambar di halaman hasil pencarian
            locators = page.locator('div[data-test-id="pin-visual-wrapper"] img')
            count = await locators.count()

            if count == 0:
                await message.edit_text("Tidak ada foto yang ditemukan.")
                await browser.close()
                return

            # Ambil maksimal 5 URL gambar
            for i in range(min(5, count)):
                img_locator = locators.nth(i)
                src = await img_locator.get_attribute('src')
                if src:
                    image_urls.append(src)

            await browser.close()

        if not image_urls:
            await message.edit_text("Gagal mengekstrak URL gambar dari Pinterest.")
            return

        await message.delete() # Hapus pesan "Mencari..."

        # Kirim gambar sebagai album jika lebih dari satu
        from telegram import InputMediaPhoto
        media_group = [InputMediaPhoto(media=url, caption=f"Hasil untuk: {query}" if i == 0 else "") for i, url in enumerate(image_urls)]

        await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_group)

    except Exception as e:
        logger.error(f"Error saat scraping Pinterest: {e}")
        await message.edit_text("Terjadi kesalahan saat mencari foto di Pinterest.")


# --- Logika untuk Jadwal JKT48 ---

async def jadwal_jkt48(update: Update, context: CallbackContext):
    """Mengambil dan mengirim jadwal konser dan event JKT48."""
    message = await update.message.reply_text("⏳ Mengambil jadwal terbaru JKT48...")

    try:
        theater_schedule = await scrape_jkt48_schedule("https://jkt48.com/theater/schedule?lang=id")
        event_schedule = await scrape_jkt48_schedule("https://jkt48.com/event/schedule?lang=id")

        if not theater_schedule and not event_schedule:
            await message.edit_text("Tidak ada jadwal yang ditemukan saat ini.")
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

        await message.edit_text(response_text, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error saat scraping jadwal JKT48: {e}")
        await message.edit_text("Terjadi kesalahan saat mengambil jadwal JKT48.")

async def jadwal_live(update: Update, context: CallbackContext):
    """Memberi tahu pengguna bahwa fitur jadwal live sedang dalam pengembangan."""
    await update.message.reply_text(
        "Fitur untuk mengambil jadwal live streaming JKT48 dari Showroom saat ini sedang dalam pengembangan.\n\n"
        "Saya akan memberitahu Anda jika fitur ini sudah siap. Terima kasih atas pengertiannya!"
    )

async def scrape_jkt48_schedule(url: str) -> list:
    """Fungsi generik untuk scrape jadwal dari situs JKT48."""
    schedule_items = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)

        # Cari semua entri jadwal
        entries = await page.locator(".entry-schedule__item").all()
        for entry in entries:
            title_element = entry.locator(".entry-schedule__item--title a")
            date_element = entry.locator(".entry-schedule__item--date")

            title = await title_element.inner_text()
            date_info = await date_element.inner_text()
            # Bersihkan dan format tanggal
            date = " ".join(date_info.split('\n'))

            schedule_items.append({"title": title.strip(), "date": date.strip()})

        await browser.close()
    return schedule_items


async def cancel(update: Update, context: CallbackContext) -> int:
    """Membatalkan percakapan."""
    await update.message.reply_text("Pencarian dibatalkan.")
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
        states={
            GET_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region_and_fetch)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Conversation handler untuk /cari_foto
    cari_foto_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("cari_foto", cari_foto_start)],
        states={
            GET_PHOTO_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_photo_query_and_fetch)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(jadwal_azan_conv_handler)
    application.add_handler(cari_foto_conv_handler)
    application.add_handler(CommandHandler("jadwal_konser", jadwal_jkt48))
    application.add_handler(CommandHandler("jadwal_live", jadwal_live))

    # Tambahkan handler lain di sini

    logger.info("Bot siap dijalankan...")
    application.run_polling()


if __name__ == '__main__':
    main()