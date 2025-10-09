#!/bin/bash

# Skrip untuk menghentikan bot Telegram yang berjalan di latar belakang.

PID_FILE="bot.pid"

# Cek apakah file PID ada
if [ ! -f "$PID_FILE" ]; then
    echo "Bot sepertinya tidak berjalan (file PID tidak ditemukan)."
    # Coba cari proses secara manual jika file PID tidak ada
    pkill -f "python3 -u bot.py"
    if [ $? -eq 0 ]; then
        echo "Menghentikan proses bot yang berjalan tanpa file PID."
    fi
    exit 1
fi

PID=$(cat "$PID_FILE")

# Cek apakah proses dengan PID tersebut ada
if ! ps -p $PID > /dev/null; then
    echo "Bot sepertinya tidak sedang berjalan (proses dengan PID $PID tidak ditemukan)."
    rm "$PID_FILE"
    exit 1
fi

echo "Menghentikan bot dengan PID: $PID..."

# Kirim sinyal TERM (15) untuk penghentian yang halus
kill $PID

# Tunggu beberapa detik
sleep 2

# Cek lagi, jika masih berjalan, paksa berhenti
if ps -p $PID > /dev/null; then
    echo "Proses tidak berhenti dengan normal, memaksa berhenti (kill -9)..."
    kill -9 $PID
fi

# Hapus file PID
rm "$PID_FILE"

echo "Bot berhasil dihentikan."