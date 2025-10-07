#!/bin/bash

# Skrip untuk menjalankan bot Telegram di latar belakang.

# Tentukan jalur absolut ke file utama bot Anda
BOT_SCRIPT="/app/bot.py"
# Tentukan nama file untuk menyimpan Process ID (PID)
PID_FILE="bot.pid"
# Tentukan nama file untuk menyimpan log
LOG_FILE="bot.log"

# Cek apakah bot sudah berjalan
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    # Cek apakah proses dengan PID tersebut benar-benar ada
    if ps -p $PID > /dev/null; then
        echo "Bot sudah berjalan dengan PID: $PID. Gunakan ./stop.sh untuk menghentikannya."
        exit 1
    else
        # Jika file PID ada tapi prosesnya tidak, hapus file PID lama
        echo "Menemukan file PID lama, tapi proses tidak berjalan. Menghapus file PID..."
        rm "$PID_FILE"
    fi
fi

echo "Memulai bot..."

# Logika Virtual Environment sengaja dinonaktifkan untuk memastikan
# bot berjalan di lingkungan Python global di mana dependensi telah diinstal.
# if [ -d "venv" ]; then
#     echo "Mengaktifkan virtual environment..."
#     source venv/bin/activate
# fi

# Jalankan bot di latar belakang menggunakan nohup
# nohup memastikan proses tetap berjalan bahkan setelah terminal ditutup
# > "$LOG_FILE" 2>&1 mengalihkan stdout dan stderr ke file log
# & menjalankan proses di latar belakang
# $! adalah PID dari proses terakhir yang dijalankan di latar belakang
nohup python3 -u "$BOT_SCRIPT" > "$LOG_FILE" 2>&1 &
PID=$!

# Simpan PID ke file
echo $PID > "$PID_FILE"

echo "Bot berhasil dimulai dengan PID: $PID."
echo "Log disimpan di: $LOG_FILE"
echo "Gunakan ./stop.sh untuk menghentikan bot."