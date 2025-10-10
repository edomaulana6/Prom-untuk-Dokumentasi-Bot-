#!/bin/bash

# Skrip untuk menghentikan bot Telegram yang berjalan di latar belakang.

# Tentukan nama file tempat Process ID (PID) disimpan
PID_FILE="bot.pid"

# Cek apakah file PID ada
if [ ! -f "$PID_FILE" ]; then
    echo "Bot sepertinya tidak sedang berjalan (file PID tidak ditemukan)."
    exit 1
fi

# Baca PID dari file
PID=$(cat "$PID_FILE")

# Cek apakah proses dengan PID tersebut ada
if ! ps -p $PID > /dev/null; then
    echo "Bot sepertinya tidak sedang berjalan (proses dengan PID $PID tidak ditemukan)."
    # Hapus file PID yang sudah tidak valid
    rm "$PID_FILE"
    exit 1
fi

echo "Menghentikan bot dengan PID: $PID..."

# Kirim sinyal TERM (15) untuk penghentian yang halus
kill $PID

# Tunggu beberapa detik untuk membiarkan proses berhenti
sleep 2

# Cek lagi apakah proses sudah benar-benar berhenti
if ps -p $PID > /dev/null; then
    echo "Proses tidak berhenti dengan normal, memaksa berhenti (kill -9)..."
    kill -9 $PID
fi

# Hapus file PID
rm "$PID_FILE"

echo "Bot berhasil dihentikan."