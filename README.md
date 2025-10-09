# Bot Telegram Serbaguna

Bot Telegram ini dirancang untuk menyediakan berbagai informasi secara cepat dan interaktif. Mulai dari jadwal sholat, pencarian gambar, hingga jadwal acara JKT48.

## Fitur

-   **/jadwal_azan <daerah>**: Mencari jadwal sholat untuk daerah tertentu di Indonesia. Jika daerah tidak disebutkan, bot akan bertanya balik.
-   **/cari_foto <query>**: Mencari dan menampilkan 5 gambar teratas dari Pinterest berdasarkan kata kunci yang diberikan. Jika kata kunci tidak ada, bot akan bertanya.
-   **/jadwal_konser**: Menampilkan jadwal pertunjukan teater dan event/konser JKT48 yang akan datang, diambil langsung dari situs resmi.
-   **/jadwal_live**: Memberikan informasi bahwa fitur jadwal live streaming dari Showroom sedang dalam pengembangan.

## Struktur Proyek

```
.
├── bot.py              # Kode utama bot
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

-   Server atau mesin Linux (termasuk Termux di Android).
-   Python 3.8 atau lebih baru.
-   `pip` (manajer paket Python).

### Langkah-langkah Instalasi

1.  **Clone repositori ini.**
    ```bash
    git clone <URL_REPOSITORI_ANDA>
    cd <NAMA_DIREKTORI>
    ```

2.  **Instal dependensi Python.**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Instal dependensi sistem dan browser untuk Playwright.**
    Ini adalah langkah **wajib** agar fitur `/cari_foto` dan `/jadwal_konser` dapat berfungsi.
    ```bash
    playwright install-deps
    playwright install
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

## Menjalankan Bot

### Menggunakan Skrip Start/Stop (Direkomendasikan)

Skrip ini memungkinkan bot berjalan di latar belakang dan tetap hidup meskipun Anda menutup terminal (misalnya di Termux atau server).

1.  **Berikan izin eksekusi pada skrip.**
    ```bash
    chmod +x start.sh
    chmod +x stop.sh
    ```

2.  **Mulai Bot.**
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

### Menjalankan Secara Manual (Untuk Debugging)
Jalankan perintah ini hanya untuk testing atau debugging. Bot akan berhenti jika Anda menutup terminal.
```bash
python3 bot.py
```