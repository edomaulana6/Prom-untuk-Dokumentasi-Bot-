# -*- coding: utf-8 -*-
# ... (seluruh script Anda)

# --- Logika Unduhan ---
async def handle_url(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    if not (url.startswith('http://') or url.startswith('https://')):
        await search_start(update, context)
        return
    keyboard = [[
        InlineKeyboardButton("🎬 Video", callback_data=f"dl|video|{url}"),
        InlineKeyboardButton("🎵 Audio", callback_data=f"dl|audio|{url}"),
    ]]
    await update.message.reply_text('Pilih format unduhan:', reply_markup=InlineKeyboardMarkup(keyboard))

# ... (seluruh script Anda)

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
                        chat_id=chat_id,
                        video=f,
                        caption=info_dict.get('title'),
                        supports_streaming=True,
                        **timeout_settings
                    )
                else:
                    await context.bot.send_audio(
                        chat_id=chat_id,
                        audio=f,
                        caption=info_dict.get('title'),
                        title=info_dict.get('title'),
                        duration=info_dict.get('duration'),
                        **timeout_settings
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
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(search_conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^dl\\|"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    logger.info("Bot siap digunakan...")
    application.run_polling()
    logger.info("Bot telah berhenti.")

if __name__ == '__main__':
    main()
