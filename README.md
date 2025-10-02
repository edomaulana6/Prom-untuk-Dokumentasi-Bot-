# Bot Telegram Pengunduh Media Canggih dengan yt-dlp

Bot Telegram ini adalah solusi lengkap untuk mengunduh video dan audio dari berbagai platform yang didukung `yt-dlp`. Dibuat dengan Python, bot ini menawarkan pengalaman pengguna yang interaktif dan visual, serta kemudahan pengelolaan bagi pemiliknya.

![Contoh Penggunaan Bot](https://i.imgur.com/example.png) <!-- Placeholder untuk screenshot -->

## Daftar Isi
- [Fitur Unggulan](#fitur-unggulan)
- [Struktur Proyek](#struktur-proyek)
- [Instalasi](#instalasi)
  - [Prasyarat](#prasyarat)
  - [Langkah-langkah Instalasi](#langkah-langkah-instalasi)
- [Konfigurasi](#konfigurasi)
  - [Mendapatkan ID Pengguna (OWNER_ID)](#mendapatkan-id-pengguna-owner_id)
- [Menjalankan Bot](#menjalankan-bot)
  - [Menggunakan Skrip Start/Stop (Direkomendasikan)](#menggunakan-skrip-startstop-direkomendasikan)
  - [Menjalankan Secara Manual](#menjalankan-secara-manual)
- [Cara Penggunaan](#cara-penggunaan)
  - [Perintah Bot](#perintah-bot)
- [Penjelasan Kode](#penjelasan-kode)
- [Tips Keamanan dan Optimasi](#tips-keamanan-dan-optimasi)

## Fitur Unggulan

- **Pencarian Visual & Interaktif**: Hasil pencarian YouTube ditampilkan dengan **thumbnail video**, judul, durasi, dan tombol unduh **Video/Audio** individual.
- **Alur Percakapan Cerdas**: Jika perintah `/search` dijalankan tanpa kata kunci, bot akan bertanya balik "Apa yang ingin Anda cari?".
- **Unduhan Langsung dari URL**: Cukup kirim URL dari situs yang didukung `yt-dlp` untuk mendapatkan pilihan unduhan Video atau Audio.
- **Notifikasi Real-time**: Pengguna akan melihat status proses yang jelas: "Mengunduh", "Mengunggah", dan notifikasi progres yang informatif.
- **Pengelolaan Mudah**: Dilengkapi skrip `start.sh` dan `stop.sh` untuk menjalankan bot di latar belakang dengan mudah.
- **Kontrol Penuh Pemilik**: Perintah `/stop` yang aman hanya dapat diakses oleh pemilik bot yang telah ditentukan.
- **Andal dan Stabil**: Penanganan error yang canggih untuk menginformasikan pengguna jika terjadi masalah, serta pembersihan file otomatis untuk menjaga server tetap bersih.

## Struktur Proyek
```
.
├── bot.py              # Kode utama bot
├── requirements.txt    # Daftar dependensi Python
├── start.sh            # Skrip untuk menjalankan bot di latar belakang
├── stop.sh             # Skrip untuk menghentikan bot
├── bot.log             # File log (dibuat oleh start.sh)
├── bot.pid             # File PID (dibuat oleh start.sh)
└── README.md           # Dokumentasi ini
```

## Instalasi

### Prasyarat

- Server atau mesin Linux (direkomendasikan untuk menjalankan bot 24/7).
- Python 3.8 atau lebih baru.
- `pip` (manajer paket Python).
- `git` (untuk mengkloning repositori).
- **FFmpeg**: Sangat penting untuk mengonversi audio ke format `.mp3`.
  - **Untuk Linux (Debian/Ubuntu):**
    ```bash
    sudo apt update && sudo apt install ffmpeg
    ```
  - **Untuk Termux (Android):**
    ```bash
    pkg update && pkg install ffmpeg
    ```

### Langkah-langkah Instalasi

1.  **Clone repositori ini.**
    ```bash
    git clone <URL_REPOSITORI_ANDA>
    cd <NAMA_DIREKTORI>
    ```

2.  **Buat dan aktifkan virtual environment (sangat direkomendasikan).**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instal dependensi Python.**
    File `requirements.txt` harus berisi:
    ```
    python-telegram-bot==20.8
    yt-dlp
    ```
    Jalankan perintah instalasi:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Instal `yt-dlp` versi terbaru langsung dari GitHub (sesuai permintaan).**
    Ini memastikan Anda mendapatkan perbaikan terbaru yang belum dirilis di `pip`.
    ```bash
    pip install --upgrade "git+https://github.com/yt-dlp/yt-dlp.git"
    ```

## Konfigurasi

Bot ini dikonfigurasi menggunakan *environment variable* untuk keamanan maksimal. Jangan pernah menulis token atau ID Anda langsung di dalam kode.

Buat file `.env` (opsional, untuk kemudahan) atau ekspor variabel langsung di shell Anda.

```sh
# Wajib diisi
export TELEGRAM_TOKEN="12345:ABC-DEF12345" # Ganti dengan token bot Anda dari @BotFather
export OWNER_ID="123456789"               # Ganti dengan ID Telegram Anda

# Anda bisa mendapatkan OWNER_ID dengan mengirim pesan ke bot @userinfobot
```

### Mendapatkan ID Pengguna (OWNER_ID)
1. Buka aplikasi Telegram.
2. Cari bot bernama `@userinfobot`.
3. Kirim pesan `/start` ke bot tersebut.
4. Bot akan membalas dengan informasi akun Anda, termasuk `Id`. Salin nomor tersebut.

## Menjalankan Bot

### Menggunakan Skrip Start/Stop (Direkomendasikan)

Skrip ini memungkinkan bot berjalan di latar belakang dan tetap hidup meskipun Anda menutup terminal.

1.  **Jadikan skrip eksekutable.**
    ```bash
    chmod +x start.sh
    chmod +x stop.sh
    ```

2.  **Mulai Bot.**
    Pastikan variabel environment (`TELEGRAM_TOKEN` dan `OWNER_ID`) sudah diatur.
    ```bash
    ./start.sh
    ```
    Bot akan berjalan di latar belakang. Progres dan error akan dicatat di `bot.log`.

3.  **Melihat Log.**
    Untuk memantau aktivitas bot secara real-time:
    ```bash
    tail -f bot.log
    ```

4.  **Hentikan Bot.**
    ```bash
    ./stop.sh
    ```

### Menjalankan Secara Manual
Jalankan perintah ini hanya untuk testing atau debugging. Bot akan berhenti jika Anda menutup terminal.
```bash
python3 bot.py
```

## Cara Penggunaan

### Perintah Bot

-   `/start`: Memulai interaksi dengan bot.
-   `/help`: Menampilkan daftar perintah.
-   `/search <kata kunci>`: Mencari video di YouTube. Hasilnya akan berupa 5 video teratas dengan thumbnail dan tombol unduh. Jika kata kunci tidak diberikan, bot akan menanyakannya.
-   `/stop`: Menghentikan bot (hanya bisa dijalankan oleh `OWNER_ID`).
-   **Kirim URL**: Langsung kirim URL dari platform yang didukung `yt-dlp` (YouTube, Twitter, dll.) untuk mendapatkan opsi unduh Video/Audio.

## Penjelasan Kode

-   `bot.py`: Menggunakan `python-telegram-bot` (v20+).
    -   `ConversationHandler`: Mengelola alur pencarian interaktif.
    -   `CallbackQueryHandler`: Menangani semua interaksi tombol (pilihan format, unduhan dari hasil pencarian).
    -   `asyncio.create_task`: Menjalankan proses unduhan dan unggahan secara asinkron agar bot tidak macet.
    -   `yt_dlp`: Dipanggil di dalam *thread* sinkron untuk melakukan pekerjaan berat (mengunduh).
    -   **Struktur Direktori**: File yang diunduh disimpan sementara di direktori `downloads/` dan dihapus secara otomatis setelah diunggah atau jika terjadi error.

## Tips Keamanan dan Optimasi

-   **Keamanan**: Selalu gunakan *environment variable* untuk data sensitif. Perintah `/stop` dilindungi dan hanya merespons `OWNER_ID`.
-   **Resource Server**: Unduhan video bisa memakan banyak CPU dan bandwidth. Batasan resolusi `720p` di dalam kode membantu mengurangi beban.
-   **Pembaruan**: `yt-dlp` sering diperbarui untuk mengatasi perubahan pada situs web. Jalankan perintah instalasi dari GitHub secara berkala untuk menjaga bot tetap berfungsi:
    ```bash
    pip install --upgrade "git+https://github.com/yt-dlp/yt-dlp.git"
    ```