# -*- coding: utf-8 -*-

"""
Bot Telegram Jadwal Sholat
Fitur:
- /jadwal_azan <daerah>
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

# State untuk ConversationHandler Jadwal Azan
GET_REGION = range(1)

# --- Handler Perintah Utama ---

async def start(update: Update, context: CallbackContext) -> None:
    """Mengirim pesan selamat datang."""
    await update.message.reply_text(
        "Halo! Saya adalah bot jadwal sholat. Gunakan /jadwal_azan <daerah> untuk memulai."
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    """Menampilkan daftar perintah."""
    await update.message.reply_text(
        "Perintah yang tersedia:\n"
        "/jadwal_azan <daerah> - Mencari jadwal sholat untuk daerah di Indonesia."
    )

# --- Logika untuk /jadwal_azan ---

async def jadwal_azan_start(update: Update, context: CallbackContext) -> int:
    """Memulai alur untuk mendapatkan jadwal azan."""
    region = " ".join(context.args)
    if region:
        await fetch_and_send_prayer_times(update, context, region)
        return ConversationHandler.END

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
        async with httpx.AsyncClient() as client:
            # 1. Cari ID kota
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
            from datetime import datetime
            today = datetime.now()
            date_str = today.strftime("%Y/%m/%d")

            prayer_url = f"https://api.myquran.com/v1/sholat/jadwal/{city_id}/{date_str}"
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

    jadwal_azan_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("jadwal_azan", jadwal_azan_start)],
        states={
            GET_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region_and_fetch)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(jadwal_azan_conv_handler)

    logger.info("Bot Jadwal Sholat siap dijalankan...")
    application.run_polling()


if __name__ == '__main__':
    main()