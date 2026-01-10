# Bot Telegram Serbaguna

Bot Telegram ini dirancang untuk menyediakan berbagai informasi secara cepat dan interaktif. Mulai dari jadwal sholat, pencarian gambar, hingga jadwal acara JKT48.

## Fitur

-   **/jadwal_azan <daerah>**: Mencari jadwal sholat untuk daerah tertentu di Indonesia. Jika daerah tidak disebutkan, bot akan bertanya balik.
-   **/cari_foto <query>**: Mencari dan menampilkan 5 gambar teratas dari Pinterest berdasarkan kata kunci yang diberikan. Jika kata kunci tidak ada, bot akan bertanya.
-   **/cari_audio <query>**: Mencari 5 video teratas dari YouTube dengan durasi di bawah 10 menit yang cocok dengan kata kunci.
-   **/jadwal_konser**: Menampilkan jadwal pertunjukan teater dan event/konser JKT48 yang akan datang, diambil langsung dari situs resmi.
-   **/jadwal_live**: Memberikan informasi bahwa fitur jadwal live streaming dari Showroom sedang dalam pengembangan.

## Struktur Proyek

```
.
├── bot.py              # Kode utama bot
├── requirements.txt    # Daftar dependensi Python
├── start.sh            # Skrip untuk menjalankan bot
├── stop.sh             # Skrip untuk menghentikan bot
├── .env                # File konfigurasi (dibuat oleh pengguna)
├── bot.log             # File log (dibuat otomatis oleh start.sh)
└── README.md           # Dokumentasi ini
```

## Instalasi

### Prasyarat

-   Server atau mesin Linux.
-   Python 3.8 atau lebih baru.
-   `pip` (manajer paket Python).
-   `nano` (editor teks, biasanya sudah terinstal di Linux).

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

1.  **Buat dan edit file `.env` menggunakan nano.**
    Perintah ini akan membuka editor teks `nano` untuk membuat dan mengedit file `.env`.
    ```bash
    nano .env
    ```

2.  **Isi file `.env`** dengan token bot Anda. Salin dan tempel baris di bawah ini ke dalam editor `nano`, lalu ganti `12345:ABC-DEF12345` dengan token bot Anda yang asli.

    ```dotenv
    # Ganti dengan token bot Anda yang didapat dari @BotFather
    TELEGRAM_TOKEN="12345:ABC-DEF12345"

    # (Opsional, tapi direkomendasikan) Ganti dengan ID Telegram numerik Anda untuk menerima notifikasi error
    # OWNER_ID="8374386811"
    ```

3.  **Simpan dan keluar dari `nano`**.
    -   Tekan `Ctrl + X`.
    -   Tekan `Y` untuk konfirmasi penyimpanan.
    -   Tekan `Enter` untuk menyimpan dengan nama `.env`.

## Menjalankan Bot

### 1. Berikan Izin Eksekusi pada Skrip
Sebelum menjalankan skrip, Anda perlu memberikannya izin untuk dieksekusi. Ini hanya perlu dilakukan sekali.
```bash
chmod +x start.sh stop.sh
```

### 2. Menjalankan Bot di Latar Belakang
Gunakan skrip `start.sh` untuk menjalankan bot. Skrip ini akan menjalankan bot di latar belakang, sehingga tetap aktif meskipun Anda menutup terminal.
```bash
./start.sh
```
Jika berhasil, Anda akan melihat pesan seperti ini:
```
Memulai bot...
Bot berhasil dimulai dengan PID: [nomor_pid].
Log disimpan di: bot.log
Gunakan ./stop.sh untuk menghentikan bot.
```

### 3. Menghentikan Bot
Untuk menghentikan bot, gunakan skrip `stop.sh`.
```bash
./stop.sh
```

## Melihat Log & Memeriksa Error

Jika bot tidak merespons atau Anda ingin melihat aktivitasnya, Anda bisa memeriksa file `bot.log`.

-   **Melihat seluruh isi log:**
    ```bash
    cat bot.log
    ```

-   **Melihat log secara real-time (live):**
    Ini sangat berguna untuk debugging. Tekan `Ctrl + C` untuk berhenti melihat.
    ```bash
    tail -f bot.log
    ```
Jika Anda menemukan pesan error di dalam log, itu akan membantu Anda memahami masalahnya. Error umum biasanya terkait dengan `TELEGRAM_TOKEN` yang salah atau masalah koneksi internet.