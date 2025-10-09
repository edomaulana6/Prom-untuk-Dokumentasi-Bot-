# Bot Telegram Jadwal Sholat

Bot Telegram sederhana dan stabil yang dirancang untuk menyediakan jadwal sholat di seluruh Indonesia. Bot ini dibuat agar ringan dan dapat diandalkan, terutama untuk dijalankan di lingkungan seperti Termux.

## Fitur

-   **/jadwal_azan <daerah>**: Mencari jadwal sholat untuk daerah tertentu di Indonesia. Jika nama daerah tidak disebutkan, bot akan bertanya balik untuk memastikan Anda mendapatkan jadwal yang benar.

## Struktur Proyek

```
.
├── bot.py              # Kode utama bot
├── requirements.txt    # Daftar dependensi Python yang ringan
├── start.sh            # Skrip untuk menjalankan bot di latar belakang
├── stop.sh             # Skrip untuk menghentikan bot
├── .env                # File konfigurasi (dibuat oleh pengguna)
├── bot.log             # File log (dibuat oleh start.sh)
└── bot.pid             # File PID (dibuat oleh start.sh)
```

## Instalasi di Termux

### Prasyarat

-   Termux di Android.
-   Python 3.8 atau lebih baru.
-   `git` (biasanya sudah terinstal di Termux).

### Langkah-langkah Instalasi

1.  **Clone repositori ini.**
    ```bash
    git clone <URL_REPOSITORI_ANDA>
    cd <NAMA_DIREKTORI>
    ```

2.  **Buat Virtual Environment (Sangat Direkomendasikan):**
    Ini akan mengisolasi dependensi bot Anda dan mencegah konflik.
    ```bash
    python3 -m venv venv
    ```

3.  **Aktifkan Virtual Environment:**
    Setiap kali Anda ingin bekerja dengan bot (menginstal dependensi atau menjalankannya), Anda harus mengaktifkan venv terlebih dahulu.
    ```bash
    source venv/bin/activate
    ```
    Anda akan melihat `(venv)` di awal prompt terminal Anda.

4.  **Instal dependensi Python.**
    Pastikan Anda berada di dalam `venv` yang aktif, lalu jalankan:
    ```bash
    pip install -r requirements.txt
    ```

## Konfigurasi

1.  **Buat file `.env`** di direktori root proyek.
    ```bash
    touch .env
    ```

2.  **Isi file `.env`** dengan token bot Anda.
    ```dotenv
    # Ganti dengan token bot Anda yang didapat dari @BotFather
    TELEGRAM_TOKEN="12345:ABC-DEF12345"
    ```

## Menjalankan Bot di Termux

### Menggunakan Skrip Start/Stop

Cara terbaik untuk menjalankan bot agar tetap hidup bahkan setelah Anda menutup Termux.

1.  **Berikan izin eksekusi pada skrip.**
    ```bash
    chmod +x start.sh
    chmod +x stop.sh
    ```

2.  **Mulai Bot.**
    Skrip ini akan secara otomatis mengaktifkan `venv` Anda sebelum menjalankan bot.
    ```bash
    ./start.sh
    ```
    Bot akan berjalan di latar belakang.

3.  **Melihat Log.**
    Untuk memantau aktivitas bot atau melihat pesan error:
    ```bash
    tail -f bot.log
    ```

4.  **Hentikan Bot.**
    ```bash
    ./stop.sh
    ```