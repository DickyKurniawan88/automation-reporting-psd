# 🤖 Automation Reporting Grafana (ILCS)

Aplikasi berbasis web (*Streamlit*) yang berfungsi untuk mengotomatisasi proses *capture* (tangkapan layar) dashboard monitoring Grafana di lingkungan ILCS. Dibangun dengan **Playwright** sebagai *engine* utama untuk memastikan hasil *capture* yang stabil, presisi, dan bebas dari panel yang masih *loading* atau "No Data".

## ✨ Fitur Utama

* **Smart Auto-Wait:** Robot akan mendeteksi indikator *loading* Grafana (seperti *icon sync-slash* dan *stop query*) dan menunggu hingga data benar-benar selesai dimuat sebelum mengambil gambar.
* **Auto-Login:** Mengotomatisasi proses autentikasi ke portal monitoring ILCS.
* **Deteksi "No Data":** Sistem akan memindai halaman untuk mencari teks "No data" dan memberikan notifikasi di tahap validasi.
* **Capture Ulang Spesifik:** Memungkinkan pengguna untuk melakukan *capture* ulang hanya pada dashboard yang bermasalah tanpa mengulang proses dari awal.
* **Dynamic Time Injection:** Menambahkan parameter waktu (Custom, Week 1-4, Monthly) secara otomatis ke dalam URL Grafana.
* **Auto-Zip & Cleanup:** Menyatukan seluruh hasil *capture* ke dalam satu file `.zip` yang rapi berdasarkan Provider, Kategori, dan Sub-Kategori, lalu menghapus data sementara (*cache*) dari server untuk keamanan.

## 📂 Struktur Repositori
```text
robot-reporting-psd/
│
├── Image/                      # Folder untuk aset visual (Case Sensitive!)
│   ├── LogoPerusahaan.png      # Logo ILCS/Pelindo di sidebar
│   └── LogoWA.png              # Logo tombol WhatsApp floating
│
├── app.py                      # Script utama aplikasi Streamlit
├── list_dashboard.xlsx         # Database daftar URL dashboard Grafana
├── requirements.txt            # Daftar library Python yang dibutuhkan
└── README.md                   # Dokumentasi proyek
```

## ⚙️ Persyaratan Sistem (*Prerequisites*)

* Python 3.9 atau lebih baru.
* Sistem operasi Windows, macOS, atau Linux (Ubuntu disarankan untuk *server deployment*).
* Koneksi internet yang stabil.

## 🚀 Panduan Instalasi & Deployment (Untuk Server Private / On-Premise)

Ikuti langkah-langkah berikut untuk menjalankan aplikasi di lingkungan *server* atau komputer lokal:

**1. Clone Repository**
```bash
git clone [https://github.com/DickyKurniawan88/robot-reporting-psd.git](https://github.com/DickyKurniawan88/robot-reporting-psd.git)
cd robot-reporting-psd
```

**2. Install Dependencies Python**
```bash
pip install -r requirements.txt
```

**3. Install Playwright & Browser Dependencies (PENTING)**
Karena aplikasi ini menggunakan *headless browser*, jalankan perintah berikut untuk mengunduh Chromium dan *dependencies* bawaan OS (wajib untuk server Linux):
```bash
playwright install chromium
playwright install-deps chromium
```

**4. Konfigurasi Secrets (Kredensial)**
Buat folder `.streamlit` di dalam *root directory* proyek, lalu buat file bernama `secrets.toml`. Isi dengan format berikut:
```toml
# .streamlit/secrets.toml

[app]
username = "admin"           # Username untuk login ke aplikasi web Streamlit
password = "password123"     # Password untuk login ke aplikasi web Streamlit

[grafana]
username = "user_ilcs"       # Username asli untuk login ke portal monitoring ILCS
password = "password_ilcs"   # Password asli untuk login ke portal monitoring ILCS
```
> **Keamanan:** File `secrets.toml` harus dimasukkan ke dalam `.gitignore` jika di-*deploy* secara lokal/on-premise agar kredensial tidak bocor.

**5. Jalankan Aplikasi**
```bash
streamlit run app.py
```

## 📝 Format Data Source (`list_dashboard.xlsx`)

Pastikan file Excel memiliki kolom dengan *header* persis seperti berikut (perhatikan besar/kecil huruf):

| Provider | Kategori | Sub_Kategori | Nama_Dashboard | URL | Tinggi_Gambar |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GCP | Data Analytic | Cluster A | Dashboard Trafik | `https://monitoring.ilcs...` | 0 |

*Keterangan:* Set `Tinggi_Gambar` ke `0` untuk *capture full page*, atau masukkan angka (contoh: `1080`) untuk memotong gambar ke tinggi tertentu.

## 🔒 Keamanan Data (*DevSecOps*)
* **Volatile Storage:** Aplikasi ini bersifat *ephemeral*. Gambar disimpan di direktori *temporary* dan langsung dihapus dari memori *server* (`shutil.rmtree`) setelah proses unduh `.zip` selesai.
* **Encrypted Secrets:** Tidak ada *password* Grafana yang di-*hardcode* di dalam skrip `app.py`.

---
*Developed for ILCS Monitoring Automation.*
```
