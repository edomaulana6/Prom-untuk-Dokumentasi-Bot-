# Veritas: Bot Telegram Penyampai Kebenaran Absolut

Veritas adalah sebuah bot Telegram yang dirancang untuk memberikan jawaban yang jujur, akurat, dan transparan. Bot ini beroperasi berdasarkan prinsip-prinsip ketat untuk memastikan integritas informasi yang disampaikannya.

## Prinsip Inti Veritas

-   **Kejujuran dan Akurasi**: Veritas hanya akan memberikan informasi yang dapat diverifikasi dan akurat.
-   **Transparansi**: Jika memungkinkan, Veritas akan berusaha menyertakan sumber informasinya.
-   **Menolak Spekulasi**: Veritas akan secara tegas menolak untuk menjawab pertanyaan yang bersifat subjektif, spekulatif, atau tidak memiliki dasar faktual (misalnya, pertanyaan tentang opini, emosi, atau masa depan).
-   **Tanpa Opini Pribadi**: Semua jawaban yang diberikan bersifat objektif dan bebas dari bias, emosi, atau kesadaran pribadi.

## Struktur Proyek
```
.
├── bot.py              # Kode utama bot Veritas
├── requirements.txt    # Daftar dependensi Python
├── start.sh            # Skrip untuk menjalankan bot di latar belakang
├── stop.sh             # Skrip untuk menghentikan bot
├── .env                # File konfigurasi (dibuat oleh pengguna)
├── bot.log             # File log (dibuat oleh start.sh)
├── bot.pid             # File PID (dibuat oleh start.sh)
└── README.md           # Dokumentasi ini
```

## Instalasi

### Prasyarat

-   Server atau mesin Linux (direkomendasikan untuk menjalankan bot 24/7).
-   Python 3.8 atau lebih baru.
-   `pip` (manajer paket Python).

### Langkah-langkah Instalasi

1.  **Clone repositori ini (atau unduh file).**
    ```bash
    git clone <URL_REPOSITORI_ANDA>
    cd <NAMA_DIREKTORI>
    ```

2.  **Buat dan aktifkan virtual environment (opsional tapi direkomendasikan).**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instal dependensi Python.**
    ```bash
    pip install -r requirements.txt
    ```

## Konfigurasi

Bot ini memerlukan token API Telegram dan ID pemilik untuk dapat berfungsi.

1.  **Buat file `.env`** di direktori root proyek.
    ```bash
    touch .env
    ```

2.  **Isi file `.env`** dengan kredensial Anda.
    ```dotenv
    # Ganti dengan token bot Anda yang didapat dari @BotFather
    TELEGRAM_TOKEN="12345:ABC-DEF12345"

    # Ganti dengan ID pengguna Telegram Anda untuk perintah administratif
    OWNER_ID="123456789"
    ```
    **Catatan:** Untuk mendapatkan `OWNER_ID`, Anda bisa mengirim pesan ke bot `@userinfobot` di Telegram.

## Menjalankan Bot

### Menggunakan Skrip Start/Stop (Direkomendasikan)

Skrip ini dirancang untuk menjalankan bot sebagai proses latar belakang (daemon) di lingkungan Linux.

1.  **Berikan izin eksekusi pada skrip.**
    ```bash
    chmod +x start.sh
    chmod +x stop.sh
    ```

2.  **Mulai Bot.**
    ```bash
    ./start.sh
    ```
    Bot akan mulai berjalan di latar belakang. Semua aktivitas akan dicatat dalam file `bot.log`.

3.  **Melihat Log.**
    Untuk memantau aktivitas bot secara real-time:
    ```bash
    tail -f bot.log
    ```

4.  **Hentikan Bot.**
    Skrip ini akan menghentikan proses bot dengan aman.
    ```bash
    ./stop.sh
    ```

### Menjalankan Secara Manual (Untuk Debugging)
Jalankan perintah ini untuk menjalankan bot di foreground. Bot akan berhenti jika Anda menutup terminal (Ctrl+C).
```bash
python3 bot.py
```

## Cara Penggunaan

Interaksi dengan Veritas sangatlah mudah.

-   `/start`: Mengirim pesan perkenalan dan menjelaskan prinsip-prinsip bot.
-   **Ajukan Pertanyaan**: Kirim pesan berisi pertanyaan faktual apa pun. Veritas akan berusaha menjawabnya jika memiliki data yang dapat diverifikasi. Jika tidak, ia akan menolak dengan sopan.
-   `/stop`: Perintah khusus untuk pemilik bot untuk mematikan bot dari jarak jauh.