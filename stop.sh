#!/bin/bash

# Skrip yang lebih tangguh untuk menghentikan bot Telegram.
# Skrip ini akan mencari proses berdasarkan nama skripnya, bukan hanya dari file PID.

BOT_SCRIPT="bot.py"
PID_FILE="bot.pid"

echo "Mencoba menghentikan bot..."

# Gunakan pkill untuk menghentikan proses bot secara andal.
# Opsi -f membuat pkill mencocokkan seluruh baris perintah, yang lebih spesifik.
# Ini akan mencari proses yang menjalankan "python3 -u bot.py" atau yang serupa.
if pgrep -f "python.*$BOT_SCRIPT" > /dev/null; then
    pkill -f "python.*$BOT_SCRIPT"
    echo "Mengirim sinyal penghentian ke proses bot..."
else
    echo "Tidak ditemukan proses bot yang berjalan."
fi

# Beri waktu sejenak agar proses benar-benar berhenti
sleep 2

# Verifikasi apakah proses masih berjalan dan paksa berhenti jika perlu
if pgrep -f "python.*$BOT_SCRIPT" > /dev/null; then
    echo "Penghentian normal gagal, mencoba menghentikan secara paksa (kill -9)..."
    pkill -9 -f "python.*$BOT_SCRIPT"
    sleep 1
fi

# Hapus file PID jika ada, untuk kebersihan
if [ -f "$PID_FILE" ]; then
    echo "Menghapus file PID lama."
    rm "$PID_FILE"
fi

# Cek terakhir untuk konfirmasi
if pgrep -f "python.*$BOT_SCRIPT" > /dev/null; then
    echo "GAGAL: Proses bot masih berjalan. Mungkin perlu diperiksa secara manual."
else
    echo "Bot berhasil dihentikan sepenuhnya."
fi