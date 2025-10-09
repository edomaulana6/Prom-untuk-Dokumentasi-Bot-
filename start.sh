#!/bin/bash

# Skrip untuk menjalankan bot Telegram di latar belakang.

BOT_SCRIPT="bot.py"
PID_FILE="bot.pid"
LOG_FILE="bot.log"

# Cek apakah bot sudah berjalan
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "Bot sudah berjalan dengan PID: $PID. Gunakan ./stop.sh untuk menghentikannya."
        exit 1
    else
        echo "File PID lama ditemukan tetapi proses tidak berjalan. Menghapus file PID..."
        rm "$PID_FILE"
    fi
fi

# Aktifkan virtual environment jika ada
if [ -d "venv" ]; then
    echo "Mengaktifkan virtual environment..."
    source venv/bin/activate
else
    echo "Peringatan: Direktori 'venv' tidak ditemukan. Menjalankan dengan Python sistem."
fi

echo "Memulai bot..."

# Jalankan bot di latar belakang menggunakan nohup
nohup python3 -u "$BOT_SCRIPT" > "$LOG_FILE" 2>&1 &
PID=$!

# Simpan PID ke file
echo $PID > "$PID_FILE"

echo "Bot berhasil dimulai dengan PID: $PID."
echo "Log disimpan di: $LOG_FILE"
echo "Gunakan ./stop.sh untuk menghentikan bot."