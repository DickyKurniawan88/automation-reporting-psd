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
