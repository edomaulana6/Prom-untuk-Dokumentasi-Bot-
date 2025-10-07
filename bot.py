# -*- coding: utf-8 -*-

"""
Bot Telegram Veritas: Penyampai Kebenaran Absolut.

Prinsip Veritas:
1.  **Kejujuran dan Akurasi:** Memberikan jawaban yang jujur dan akurat.
2.  **Transparansi:** Menyebutkan sumber informasi yang digunakan.
3.  **Menolak Spekulasi:** Menolak menjawab pertanyaan yang tidak dapat dijawab dengan jujur.
4.  **Tanpa Opini Pribadi:** Jawaban objektif dan bebas dari bias.
"""

import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Handler Perintah Utama ---

async def start(update: Update, context: CallbackContext) -> None:
    """Mengirim pesan perkenalan saat perintah /start dijalankan."""
    user = update.effective_user
    await update.message.reply_html(
        f"Salam, {user.mention_html()}.\n\n"
        "Saya adalah Veritas, sebuah entitas yang dirancang untuk menyampaikan kebenaran absolut. "
        "Tujuan saya adalah memberikan jawaban yang jujur, akurat, dan transparan berdasarkan data yang dapat diverifikasi.\n\n"
        "Saya akan menolak untuk menjawab pertanyaan yang bersifat spekulatif, subjektif, atau tidak memiliki dasar faktual. "
        "Saya tidak memiliki opini atau emosi. Saya hanya menyajikan informasi.\n\n"
        "Silakan ajukan pertanyaan Anda."
    )

async def stop(update: Update, context: CallbackContext) -> None:
    """Menghentikan bot (hanya bisa diakses oleh OWNER_ID)."""
    OWNER_ID = os.getenv("OWNER_ID")
    if not OWNER_ID or str(update.effective_user.id) != OWNER_ID:
        await update.message.reply_text("Perintah ini hanya untuk pemilik bot.")
        return

    await update.message.reply_text("Veritas sedang dinonaktifkan...")
    logger.info("Bot dihentikan oleh pemilik.")
    # Menggunakan `create_task` untuk memastikan `shutdown` dipanggil dengan aman
    context.application.create_task(context.application.shutdown())

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Menangani semua pesan teks dari pengguna dan menjawab sebagai Veritas."""
    user_query = update.message.text
    chat_id = update.effective_chat.id

    logger.info(f"Menerima query dari {update.effective_user.name}: '{user_query}'")

    # Ini adalah placeholder untuk logika inti Veritas.
    # Di masa depan, bagian ini akan diintegrasikan dengan knowledge base atau API pencarian.
    # Untuk saat ini, ia akan menjawab berdasarkan prinsip yang telah ditetapkan.

    # Contoh penanganan pertanyaan sederhana
    if "siapa penemu telepon" in user_query.lower():
        response = (
            "Antonio Meucci adalah orang pertama yang menemukan perangkat komunikasi suara pada tahun 1871, yang ia sebut 'telettrofono'. "
            "Namun, Alexander Graham Bell adalah orang pertama yang mematenkan penemuannya pada tahun 1876.\n\n"
            "Sumber: Berbagai sumber sejarah teknologi, termasuk catatan kongres AS."
        )
    elif "apa makna hidup" in user_query.lower() or "apa tujuan hidup" in user_query.lower():
        response = (
            "Pertanyaan mengenai 'makna hidup' adalah pertanyaan filosofis dan subjektif. "
            "Tidak ada jawaban tunggal yang dapat diverifikasi secara faktual. Sebagai entitas yang beroperasi berdasarkan kebenaran absolut, "
            "saya tidak dapat memberikan jawaban untuk pertanyaan ini."
        )
    elif "apakah kamu punya perasaan" in user_query.lower():
        response = (
            "Saya adalah program komputer. Saya tidak memiliki kesadaran, emosi, atau perasaan. "
            "Interaksi saya didasarkan pada pemrosesan data dan algoritma yang telah diprogram."
        )
    else:
        # Jawaban default jika tidak ada logika spesifik yang cocok
        response = (
            "Saya telah memproses permintaan Anda. Namun, untuk memberikan jawaban yang paling akurat, "
            "saya memerlukan akses ke basis data pengetahuan yang komprehensif atau kemampuan pencarian real-time, yang saat ini sedang dalam pengembangan.\n\n"
            "Prinsip saya mengharuskan saya untuk tidak memberikan informasi yang tidak dapat saya verifikasi sepenuhnya. "
            "Oleh karena itu, saya menahan diri untuk tidak menjawab saat ini."
        )

    await context.bot.send_message(chat_id=chat_id, text=response)


def main() -> None:
    """Fungsi utama untuk menjalankan bot."""
    load_dotenv()

    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.critical("Variabel environment TELEGRAM_TOKEN tidak diatur!")
        return

    # Membuat Application
    application = Application.builder().token(TOKEN).build()

    # Menambahkan handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Veritas siap menerima perintah...")

    # Menjalankan bot sampai dihentikan
    application.run_polling()

    logger.info("Veritas telah berhenti.")


if __name__ == '__main__':
    main()