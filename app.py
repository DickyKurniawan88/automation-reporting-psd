import json
import asyncio
import sys
import streamlit as st
import pandas as pd
import os
os.system("playwright install chromium")
import zipfile
import re
import calendar
import time
import tempfile
import shutil
import io
import urllib.request
from datetime import datetime
from PIL import Image
import base64

# ==========================================
#  FIX UNTUK WINDOWS (MENCEGAH CRASH NOTIMPLEMENTEDERROR)
# ==========================================
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ==========================================
#  IMPORT PLAYWRIGHT
# ==========================================
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# ==========================================
#  KONFIGURASI USER & FOLDER
# ==========================================
USERNAME_ILCS = st.secrets["grafana"]["username"]
PASSWORD_ILCS = st.secrets["grafana"]["password"]
NAMA_FILE_EXCEL = 'list_dashboard.xlsx'
FOLDER_PROFILE = os.path.join(os.getcwd(), 'chrome_data_playwright')

# ==========================================
#  FUNGSI BANTUAN (HELPER)
# ==========================================
def image_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def get_epoch_from_str(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp() * 1000)

def get_indo_month_name(month_int):
    bulan_indo = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    return bulan_indo.get(month_int, str(month_int))

def clean_filename(text):
    if pd.isna(text): return "General"
    return re.sub(r'[\\/*?:"<>|]', "", str(text)).strip()

def format_waktu(detik_total):
    detik_total = int(detik_total)
    jam = detik_total // 3600
    menit = (detik_total % 3600) // 60
    detik = detik_total % 60
    if jam > 0: return f"{jam}j {menit}m {detik}s"
    elif menit > 0: return f"{menit}m {detik}s"
    else: return f"{detik}s"

def update_ui_progress(start_time, tugas_selesai, total_tugas, ui_placeholder):
    if ui_placeholder and start_time and total_tugas > 0:
        elapsed = time.time() - start_time
        sisa_tugas = total_tugas - tugas_selesai
        
        if tugas_selesai > 0:
            avg_time = elapsed / tugas_selesai
            eta_seconds = avg_time * sisa_tugas
            eta_str = format_waktu(eta_seconds)
        else:
            eta_str = "Menghitung kecepatan..."
            
        teks_ui = f"""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
            <strong>⏱️ Waktu Berjalan:</strong> <span style="color:#ff4b4b; font-size:18px;">{format_waktu(elapsed)}</span> &nbsp; | &nbsp; 
            <strong>⏳ Estimasi Selesai:</strong> <span style="color:#0068c9; font-size:18px;">{eta_str}</span><br>
            <div style="margin-top: 8px;">📊 <strong>Progress:</strong> Selesai <strong>{tugas_selesai}</strong> dari <strong>{total_tugas}</strong> capture (Sisa: {sisa_tugas})</div>
        </div>
        """
        ui_placeholder.markdown(teks_ui, unsafe_allow_html=True)

def inject_absolute_time(url, start_ms, end_ms):
    if pd.isna(url): return ""
    if "monitoring.ilcs.co.id" not in url and "grafana" not in url: return url
    
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    query_params['from'] = [str(start_ms)]
    query_params['to'] = [str(end_ms)]
    
    interval_vars = ['var-alignmentPeriod', 'var-interval']
    found_interval = False
    
    for var in interval_vars:
        if var in query_params:
            query_params[var] = ['1h']
            found_interval = True
            
    if not found_interval:
        query_params['var-interval'] = ['1h']
        
    return urlunparse((
        parsed.scheme, parsed.netloc, parsed.path, 
        parsed.params, urlencode(query_params, doseq=True), parsed.fragment
    ))

def atur_tinggi_gambar(image_path, target_height):
    try:
        img = Image.open(image_path)
        width, current_height = img.size
        if target_height > 0 and target_height < current_height:
            img.crop((0, 0, width, target_height)).save(image_path)
    except: pass

def zip_folder_to_memory(folder_path):
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
    memory_file.seek(0)
    return memory_file

def tampilkan_tombol_wa():
        wa_path = os.path.join("Image", "LogoWA.png")
        if os.path.exists(wa_path):
            wa_html = f'<a href="https://wa.me/6287806777808?text=Assalamualaikum,%20Mas%20Dicky" target="_blank" class="wa-float"><img src="data:image/png;base64,{image_to_base64(wa_path)}" alt="WhatsApp"></a><style>.wa-float {{ position: fixed; width: 60px; height: 60px; bottom: 40px; right: 40px; background-color: transparent; border-radius: 50px; text-align: center; z-index: 9999; box-shadow: 2px 2px 10px rgba(0,0,0,0.3); transition: transform 0.3s ease-in-out; }} .wa-float img {{ width: 100%; height: 100%; border-radius: 50%; }} .wa-float:hover {{ transform: scale(1.1); }} </style>'
            st.markdown(wa_html, unsafe_allow_html=True)
        else:
            st.error(f"Peringatan Debugging: File {wa_path} tidak terdeteksi oleh sistem!")

# FITUR BARU: Mengecek koneksi internet secara native tanpa library eksternal
def cek_koneksi_internet():
    try:
        urllib.request.urlopen('http://www.google.com', timeout=3)
        return True
    except:
        return False

# ==========================================
#  FUNGSI PLAYWRIGHT UTAMA
# ==========================================
def login_otomatis_playwright(page, status_container):
    status_container.write("🔐 Mengecek status login...")
    try:
        page.goto("https://monitoring.ilcs.co.id/", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000) 
        
        input_user = page.locator("input[name='user']")
        if input_user.is_visible():
            status_container.write("Sedang mengisi form login otomatis...")
            input_user.fill(USERNAME_ILCS)
            page.locator("input[name='password']").fill(PASSWORD_ILCS)
            page.locator("input[name='password']").press("Enter")
            status_container.write("⏳ Menunggu autentikasi server...")
            page.wait_for_timeout(8000) 
            status_container.write("✅ Login berhasil diproses.")
        else:
            status_container.write("✅ Session masih aktif (Sudah login).")
    except Exception as e:
        status_container.warning(f"Info Login: {str(e)[:50]}")

def capture_ulang_single(item):
    try:
        # Cek internet sebelum melakukan sesuatu
        if not cek_koneksi_internet():
            return False, True # Dianggap gagal capture dan masih no data
            
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=FOLDER_PROFILE, headless=True,
                viewport={'width': 3840, 'height': 2160},
                device_scale_factor=2,  
                args=["--disable-gpu", "--disable-dev-shm-usage"]
            )
            page = browser.pages[0] if len(browser.pages) > 0 else browser.new_page()
            
            try:
                page.goto("https://monitoring.ilcs.co.id/", wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)
                if page.locator("input[name='user']").is_visible():
                    page.locator("input[name='user']").fill(USERNAME_ILCS)
                    page.locator("input[name='password']").fill(PASSWORD_ILCS)
                    page.locator("input[name='password']").press("Enter")
                    page.wait_for_timeout(8000)
            except: pass

            timeout_limit = 180000 if item['label'].lower() == 'monthly' else 90000
            max_tunggu = 150000 if 'load balancer' in str(item['nama_dash']).lower() or item['label'].lower() == 'monthly' else 90000

            page.goto(item['url'], wait_until="commit", timeout=timeout_limit)
            try: page.wait_for_selector("body", timeout=60000);
            except: pass
            try: page.wait_for_load_state("networkidle", timeout=max_tunggu)
            except: pass 
            
            # 1. Cek panel loading sampai hilang
            try: page.wait_for_selector(".panel-loading, [class*='spin'], [class*='loading']", state="hidden", timeout=max_tunggu)
            except: pass 
            
            # ---> JEDA NAPAS PERTAMA: Kasih 3 detik biar Grafana mencerna data yang baru ditarik
            page.wait_for_timeout(3000)
            # --------------------------------------------------------------------------------------------------------
            # 2. Cek elemen grafik (canvas) sampai kelihatan di layar
            try: page.wait_for_selector("canvas", state="visible", timeout=30000)
            except: pass
            
            # ---> JURUS 1: SCROLL PANCINGAN <---
            # Gulir mouse ke bawah dan ke atas biar Grafana sadar dan ngerender semua panel
            try:
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(2000)
                page.mouse.wheel(0, -1500)
                page.wait_for_timeout(2000)
            except: pass
            try:
                for _ in range(15): 
                    stop_query_count = page.locator("[aria-label='Stop query'], [title='Stop query'], [data-testid='icon-sync-slash']").count()
                    if stop_query_count == 0:
                        break 
                    page.wait_for_timeout(5000) 
            except: pass
            page.wait_for_timeout(10000) # Jeda napas standar

            # CEK PERTAMA: Apakah grafiknya masih zonk? (tambah N/A)
            masih_no_data = page.evaluate("() => /No data|No Data|N\\/A/i.test(document.body.innerText)")

            # ---> JURUS 2: FORCE REFRESH KALAU ZONK <---
            if masih_no_data:
                try:
                    # Coba klik tombol "Refresh dashboard" bawaan Grafana di pojok kanan atas
                    btn_refresh = page.locator("button[aria-label='Refresh dashboard'], button[title='Refresh dashboard']")
                    if btn_refresh.is_visible():
                        btn_refresh.click()
                    else:
                        page.reload(wait_until="commit") # Kalau tombol ga ketemu, reload paksa tab-nya
                    
                    page.wait_for_timeout(5000) # Tunggu Grafana bereaksi
                    
                    # Nungguin ulang kueri Grafana (kesempatan kedua, sabar sampai 45 detik)
                    for _ in range(9): 
                        if page.locator("[aria-label='Stop query']").count() == 0:
                            break 
                        page.wait_for_timeout(5000)
                        
                    # Kasih napas ekstra 15 detik buat jaminan grafik berat kelar dirender
                    page.wait_for_timeout(15000)
                except:
                    page.wait_for_timeout(20000) # Fallback kalau error
                
                # Cek hasil akhir setelah dipaksa refresh
                masih_no_data = page.evaluate("() => /No data|No Data|N\\/A/i.test(document.body.innerText)")

            # -------------------------------------------------------------------------------------------------------------
            page.screenshot(path=item['path'])
            if item['target_px'] > 0: atur_tinggi_gambar(item['path'], item['target_px'] * 2)
            
            browser.close()
            return True, masih_no_data
    except Exception as e:
        return False, True


# ==========================================
#  INISIALISASI STATE UTAMA
# ==========================================
st.set_page_config(page_title="Automation Reporting Grafana", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'status_aplikasi' not in st.session_state:
    st.session_state.status_aplikasi = "idle"
if 'hasil_capture' not in st.session_state:
    st.session_state.hasil_capture = []
if 'base_output_dir' not in st.session_state:
    st.session_state.base_output_dir = ""
if 'temp_parent_dir' not in st.session_state:
    st.session_state.temp_parent_dir = ""

# ==========================================
#  SISTEM LOGIN MENGGUNAKAN FORM
# ==========================================
if not st.session_state.logged_in:
    # injeksi css khusus untuk mengunci layar login (no scroll) + animasi imut
    st.markdown("""
        <style>
        /* kunci mentok html dan body */
        html, body {
            overflow: hidden !important;
            height: 100vh !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* kunci wadah aplikasi utama streamlit */
        div[data-testid="stappviewcontainer" i], 
        div[data-testid="stmain" i], 
        div[data-testid="stappviewblockcontainer" i] {
            overflow: hidden !important;
            height: 100vh !important;
        }
        
        /* sembunyikan header kosong bawaan streamlit */
        header {
            display: none !important;
        }
        
        /* --- CSS ANIMASI IMUT --- */
        @keyframes ngambang {
            0% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-15px) rotate(5deg); }
            100% { transform: translateY(0px) rotate(0deg); }
        }
        .robot-imut {
            font-size: 70px;
            text-align: center;
            display: block;
            animation: ngambang 3s ease-in-out infinite;
            margin-bottom: -15px;
        }
        </style>
    """, unsafe_allow_html=1)

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1.5, 2, 1.5])
    
    with col_login:
        # Panggil class animasi robotnya di sini
        st.markdown('<div class="robot-imut">🤖</div>', unsafe_allow_html=1)
        st.markdown('<h1 style="text-align: center;">Login Sistem</h1>', unsafe_allow_html=1)
        st.info("Silakan masukkan Kredensial untuk mengakses Automation Reporting.")
        
        with st.form("form_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            btn_login = st.form_submit_button("Masuk", type="primary", use_container_width=True)
            
            if btn_login:
                if username == st.secrets["app"]["username"] and password == st.secrets["app"]["password"]:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Username atau Password salah!")
    
    st.stop()# ==========================================
#  KODE UI UTAMA (SETELAH LOGIN BERHASIL)
# ==========================================
tampilkan_tombol_wa()

col_kiri, col_kanan = st.columns([1.8, 1.2]) 

with col_kanan:
    st.markdown("### 📂 Data Source Info")
    if os.path.exists(NAMA_FILE_EXCEL):
        try:
            df = pd.read_excel(NAMA_FILE_EXCEL)
            if 'Tinggi_Gambar' not in df.columns: df['Tinggi_Gambar'] = 0
            df = df.sort_values(by=['Provider', 'Kategori', 'Sub_Kategori'])
            total_dash = len(df)
            st.success(f"✅ Terhubung: {NAMA_FILE_EXCEL}")
            st.info(f"Total: **{total_dash} Dashboard**")
            with st.expander("🔍 Preview Isi Data", expanded=True):
                st.dataframe(df[['Provider', 'Nama_Dashboard']], width="stretch", height=300)
        except Exception as e:
            st.error(f"File rusak/error: {e}")
            st.stop()
    else:
        st.error(f"❌ File '{NAMA_FILE_EXCEL}' Tidak Ditemukan!")
        st.stop()
#------------------------------------------------------------------------------------------------------------------------------------------------------------
with st.sidebar:
    img_path = os.path.join("Image", "LogoPerusahaan.png")
    try:
        st.markdown(f'<a href="https://www.ilcs.co.id/" target="_blank"><img src="data:image/png;base64,{image_to_base64(img_path)}" style="width:100%; border-radius:8px;" draggable="false"></a><br><br>', unsafe_allow_html=True)
    except: pass

    st.header("⚙️ Konfigurasi Waktu")
    #update
    if st.session_state.status_aplikasi == "idle":
        pilihan_mode = st.radio("Pilih Mode Periode:", ('Custom Range', 'Full Batch (Week 1-4 & Monthly)', 'Single Preset', 'Multi Select'))

        configs = []
        today = datetime.now()
        root_name_zip = "Report"

        if pilihan_mode == 'Custom Range':
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Mulai", today)
            end_date = col2.date_input("Akhir", today)
            if st.checkbox("Gunakan Tanggal Ini"):
                 root_name_zip = f"Laporan_Custom_{start_date}"
                 configs.append({'label': 'custom_range', 'start': f"{start_date} 00:00:00", 'end': f"{end_date} 23:59:59"})
        else:
            col_y, col_m = st.columns(2)
            tahun = col_y.number_input("Tahun", value=today.year)
            bulan = col_m.number_input("Bulan", value=today.month, min_value=1, max_value=12)
            last_day = calendar.monthrange(tahun, bulan)[1]
            root_name_zip = f"{get_indo_month_name(bulan)}_{tahun}"
            
            definitions = {
                'Week 1': {'key': 'week1',   'start': f"{tahun}-{bulan:02d}-01 00:00:00", 'end': f"{tahun}-{bulan:02d}-07 23:59:59"},
                'Week 2': {'key': 'week2',   'start': f"{tahun}-{bulan:02d}-08 00:00:00", 'end': f"{tahun}-{bulan:02d}-14 23:59:59"},
                'Week 3': {'key': 'week3',   'start': f"{tahun}-{bulan:02d}-15 00:00:00", 'end': f"{tahun}-{bulan:02d}-21 23:59:59"},
                'Week 4': {'key': 'week4',   'start': f"{tahun}-{bulan:02d}-22 00:00:00", 'end': f"{tahun}-{bulan:02d}-28 23:59:59"},
                'Monthly': {'key': 'monthly', 'start': f"{tahun}-{bulan:02d}-01 00:00:00", 'end': f"{tahun}-{bulan:02d}-{last_day:02d} 23:59:59"},
            }
            if pilihan_mode == 'Full Batch (Week 1-4 & Monthly)':
                for k, val in definitions.items(): configs.append({'label': val['key'], 'start': val['start'], 'end': val['end']})
            elif pilihan_mode == 'Single Preset':
                pilih_satu = st.selectbox("Pilih Periode:", list(definitions.keys()))
                configs.append({'label': definitions[pilih_satu]['key'], 'start': definitions[pilih_satu]['start'], 'end': definitions[pilih_satu]['end']})
            elif pilihan_mode == 'Multi Select':
                for item in st.multiselect("Pilih Periode:", list(definitions.keys())): 
                    configs.append({'label': definitions[item]['key'], 'start': definitions[item]['start'], 'end': definitions[item]['end']})

        st.divider()
        if st.button("🚀 JALANKAN ROBOT", type="primary", width="stretch"):
            if not configs: st.error("⚠️ Harap tentukan konfigurasi waktu!")
            else:
                st.session_state.configs = configs
                st.session_state.root_name_zip = root_name_zip
                st.session_state.status_aplikasi = "konfirmasi"
                st.rerun()
            
    # ---> TAMPILAN KALAU ROBOT LAGI JALAN / VALIDASI <---
    else:
        st.info("🔒 Konfigurasi Waktu dikunci.")
        st.markdown("<small>Selesaikan proses saat ini atau klik tombol <b>Reset/Kembali ke Beranda</b> untuk mengatur ulang waktu laporan.</small>", unsafe_allow_html=True)

#=================================================================================================================================================================
with col_kiri:
    if st.session_state.status_aplikasi == "idle":
        st.title("🤖 Automation Reporting (Playwright Engine)")
        st.markdown("Dashboard ini menjalankan Reporting Grafana secara otomatis berdasarkan data di sebelah kanan.")
        st.divider()
        st.info("Pilih konfigurasi waktu di Sidebar, lalu klik **JALANKAN ROBOT**.")

    elif st.session_state.status_aplikasi == "konfirmasi":
        st.title("⚠️ Konfirmasi Sistem")
        st.divider()
        st.warning("Pastikan kamu menggunakan device **PC/Laptop**. Sistem kini menggunakan **Playwright Engine** untuk stabilitas.")
        c1, c2 = st.columns(2)
        with c2:
            if st.button("✅ Lanjut Mulai Proses", type="primary", width="stretch"):
                st.session_state.status_aplikasi = "running"; st.rerun()
        with c1:
            if st.button("❌ Batal", width="stretch"):
                st.session_state.status_aplikasi = "idle"; st.rerun()
#----------------------------------------------------------------------------------
    elif st.session_state.status_aplikasi == "running":
        st.title("🤖 Robot Sedang Bekerja...")
        st.info("💡 **Engine:** Playwright Auto-Wait dengan Tab Management Memory Safe.")
        if st.button("🔄 Layar Nyangkut? Klik Disini (Reset)", width="stretch"):
            st.session_state.status_aplikasi = "idle"; st.rerun()
        st.divider()
        
        progress_bar = st.progress(0)
        info_waktu_ui = st.empty() 
        status_text = st.status("Menyiapkan Sistem Playwright...", expanded=True)
        
        try:
            # ---> AMBIL LAGI INGATAN DARI SESSION STATE <---
            configs = st.session_state.configs
            root_name_zip = st.session_state.root_name_zip
            
            temp_parent = os.path.join(os.getcwd(), "FOLDER_HASIL_SEMENTARA")
            os.makedirs(temp_parent, exist_ok=True)
            
            st.session_state.temp_parent_dir = temp_parent
            base_output_dir = os.path.join(temp_parent, root_name_zip)
            st.session_state.base_output_dir = base_output_dir
            os.makedirs(base_output_dir, exist_ok=True)
            
            # ---> [DITAMBAHKAN] Deklarasi letak file JSON untuk menyimpan memori
            log_file = os.path.join(temp_parent, "log_status.json")
            
            # CEK APAKAH INI RUN BARU ATAU LANJUTAN
            if 'hasil_capture' not in st.session_state or not st.session_state.hasil_capture:
                # ---> [DIRUBAH] Kalau list kosong, robot disuruh baca file JSON dulu. 
                # Kalau JSON-nya ada, masukin isinya ke memori. Kalau gak ada, bikin list kosong.
                if os.path.exists(log_file):
                    with open(log_file, "r") as f:
                        st.session_state.hasil_capture = json.load(f)
                else:
                    st.session_state.hasil_capture = []

            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=FOLDER_PROFILE,
                    headless=True,
                    viewport={'width': 1920, 'height': 1080},
                    device_scale_factor=2, 
                    args=["--disable-gpu", "--disable-dev-shm-usage"]
                )
                
                # Buka 1 tab khusus untuk Login
                page_login = browser.pages[0] if len(browser.pages) > 0 else browser.new_page()
                login_otomatis_playwright(page_login, status_text)
                # Biarkan page_login tetap terbuka agar session tetap terjaga
                
                total_tugas_asli = total_dash * len(configs)
                tugas_berjalan = 0
                waktu_mulai = time.time()
                
                status_text.write(f"⏳ Total antrean: {total_tugas_asli} Capture...")
                
                for index, row in df.iterrows():
                    nama_dash = row['Nama_Dashboard']
                    url_asli  = row['URL']
                    provider  = clean_filename(row['Provider'])
                    kategori  = clean_filename(row['Kategori'])
                    sub_kat   = clean_filename(row['Sub_Kategori'])
                    
                    try: target_px = int(row['Tinggi_Gambar']) if pd.notna(row['Tinggi_Gambar']) else 0
                    except: target_px = 0
                    
                    if pd.isna(url_asli): continue

                    target_dir = os.path.join(base_output_dir, provider, kategori, sub_kat, clean_filename(nama_dash))
                    os.makedirs(target_dir, exist_ok=True)

                    for config in configs:
                        # --- Cek Koneksi Internet DULU ---
                        if not cek_koneksi_internet():
                            raise Exception("Koneksi Internet Terputus! Proses dibatalkan untuk mencegah error massal.")
                            
                        label = config['label']

                        filename_cek = os.path.join(target_dir, f"{label}.png")
                        
                        if os.path.exists(filename_cek):
                            # ---> [DITAMBAHKAN] Cek status No Data dari JSON memory pas proses nge-skip
                            ada_no_data = any(item['path'] == filename_cek and item['ada_no_data'] for item in st.session_state.hasil_capture)
                            tanda_nodata = "⚠️ NO DATA" if ada_no_data else "✅"
                            
                            # ---> [DIRUBAH] UI nampilin info apakah gambar yang di-skip ini No Data atau nggak
                            status_text.write(f"⏩ [{tugas_berjalan+1}/{total_tugas_asli}] Skip: **{nama_dash}** ({label}) - {tanda_nodata}")
                            
                            # ---> [DITAMBAHKAN] Mencegah bug data ilang. Pastikan gambar yg di-skip tetap masuk antrean validasi
                            if not any(item['path'] == filename_cek for item in st.session_state.hasil_capture):
                                url_target_fallback = inject_absolute_time(url_asli, get_epoch_from_str(config['start']), get_epoch_from_str(config['end']))
                                st.session_state.hasil_capture.append({
                                    'nama_dash': nama_dash, 'label': label,
                                    'path': filename_cek, 'url': url_target_fallback,
                                    'target_px': target_px, 'ada_no_data': False # Default fallback
                                })

                            tugas_berjalan += 1
                            progress_bar.progress(tugas_berjalan / total_tugas_asli)
                            continue # Langsung lompat ke dashboard selanjutnya!
                        
                        status_text.write(f"⏳ [{tugas_berjalan+1}/{total_tugas_asli}] Memproses: **{nama_dash}** ({label}) ...")
                        update_ui_progress(waktu_mulai, tugas_berjalan, total_tugas_asli, info_waktu_ui)
                        
                        url_target = inject_absolute_time(url_asli, get_epoch_from_str(config['start']), get_epoch_from_str(config['end']))
                        if provider == 'GCP' and 'data analytic' in str(nama_dash).lower():
                            url_target += "&var-cluster_name=data-analytic" if "?" in url_target else "?var-cluster_name=data-analytic"

                        # --- Buka Tab Baru Khusus Dashboard Ini (RAM Safe) ---
                        page_baru = browser.new_page()

                        try:
                            timeout_limit = 180000 if label.lower() == 'monthly' else 90000
                            max_tunggu = 150000 if 'load balancer' in str(nama_dash).lower() or label.lower() == 'monthly' else 90000

                            page_baru.goto(url_target, wait_until="commit", timeout=timeout_limit)

                            try:
                                page_baru.wait_for_selector("body", timeout=60000)
                                page_baru.evaluate("document.body.style.zoom='50%'")
                            except: pass
                            
                            try: page_baru.wait_for_load_state("networkidle", timeout=max_tunggu)
                            except: pass 

                            try: page_baru.wait_for_selector(".panel-loading, [class*='spin'], [class*='loading']", state="hidden", timeout=max_tunggu)
                            except PlaywrightTimeoutError: pass 
                            
                            try: page_baru.wait_for_selector("canvas", state="visible", timeout=30000)
                            except PlaywrightTimeoutError: pass

                            try:
                                for _ in range(15): 
                                    stop_query_count = page_baru.locator("[aria-label='Stop query'], [title='Stop query'], [data-testid='icon-sync-slash']").count()
                                    if stop_query_count == 0:
                                        break 
                                    page_baru.wait_for_timeout(10000) 
                            except: pass

                            page_baru.wait_for_timeout(5000)
                        
                            ada_no_data = page_baru.evaluate("() => /No data|No Data/i.test(document.body.innerText)")
                            
                            filename = os.path.join(target_dir, f"{label}.png")
                            page_baru.screenshot(path=filename)
                            if target_px > 0: atur_tinggi_gambar(filename, target_px * 2)

                            # ---> [DIRUBAH] Sapu bersih duplikat. Kalau file path ini udah ada di memori, hapus dulu biar gak dobel
                            st.session_state.hasil_capture = [i for i in st.session_state.hasil_capture if i['path'] != filename]

                            st.session_state.hasil_capture.append({
                                'nama_dash': nama_dash, 'label': label,
                                'path': filename, 'url': url_target,
                                'target_px': target_px, 'ada_no_data': ada_no_data
                            })

                            # ---> [DITAMBAHKAN] Tulis memori ini ke file JSON di harddisk server (Save Checkpoint!)
                            with open(log_file, "w") as f:
                                json.dump(st.session_state.hasil_capture, f)

                            b64_img = image_to_base64(filename)
                            tanda_nodata = "⚠️ NO DATA" if ada_no_data else "✅"
                            html_preview = f"""
                            <details>
                                <summary style="cursor: pointer; padding: 6px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 5px;">
                                    📸 [{tugas_berjalan+1}/{total_tugas_asli}] {tanda_nodata}: {nama_dash} ({label})
                                </summary>
                                <div style="margin-top: 10px; border: 1px solid #ccc; padding: 5px;"><img src="data:image/png;base64,{b64_img}" style="width: 100%;"></div>
                            </details>
                            """
                            status_text.markdown(html_preview, unsafe_allow_html=True)

                        except Exception as e:
                            status_text.write(f"⚠️ Gagal capture {label}: {str(e)[:100]}")
                        finally:
                            # Selalu tutup tab setelah selesai urusan agar RAM lega
                            page_baru.close()
                        
                        tugas_berjalan += 1
                        progress_bar.progress(tugas_berjalan / total_tugas_asli)

                browser.close() 
            #-----------------------------------------------------------------------------------

            waktu_total = time.time() - waktu_mulai
            info_waktu_ui.markdown(f'<div style="background-color: #d1e7dd; padding: 15px; border-radius: 10px; border-left: 5px solid #0f5132;"><strong>🎉 Proses Selesai!</strong> Total waktu: {format_waktu(waktu_total)}<br>Berhasil menyelesaikan <strong>{total_tugas_asli}</strong> capture.</div>', unsafe_allow_html=True)
            
            status_text.update(label="✅ Capture Selesai. Masuk ke tahap validasi...", state="complete", expanded=False)
            st.session_state.status_aplikasi = "validasi"
            st.rerun()
            
        except Exception as e:
            st.error(f"🚨 {e}")
            if st.button("Reset Sistem"): 
                st.session_state.status_aplikasi = "idle"
                st.rerun()

    # --- STATE 4: VALIDASI ---
    elif st.session_state.status_aplikasi == "validasi":
        st.title("🔎 Validasi Hasil Capture")
        st.info("Sistem mendeteksi tulisan **'No data'**. Kamu bisa Capture Ulang secara satuan khusus untuk gambar tersebut.")
        
        item_bermasalah = [item for item in st.session_state.hasil_capture if item['ada_no_data']]
        # ---> BONGKAR ISI MEMORI ROBOT <---
        st.write("🛑 CEK DATA MENTAH DARI JSON:")
        st.json(item_bermasalah)
        
        if not item_bermasalah:
            st.success("🎉 Luar biasa! Tidak ditemukan satupun panel 'No data' di seluruh dashboard.")
        else:
            st.warning(f"⚠️ Ditemukan **{len(item_bermasalah)}** gambar dengan indikasi 'No data'.")
            st.divider()
            
            for idx, item in enumerate(item_bermasalah):
                c1, c2 = st.columns([3, 1])
                with c1:
                    # 1. Hapus caption bawaannya
                    st.image(item['path'], width="stretch")
                    # 2. Bikin custom caption berupa link yang bisa diklik (warna biru dan buka tab baru)
                    st.markdown(f"<div style='text-align: center; margin-top: -10px;'><a href='{item['url']}' target='_blank' style='color: #1f77b4; text-decoration: none; font-size: 14px;'>🔗 <b>{item['nama_dash']} - Periode: {item['label']}</b></a></div><br>", unsafe_allow_html=True)
                with c2:
                    st.write("") # Spacer
                    st.write("")
                    if st.button(f"🔄 Capture Ulang", key=f"btn_recapture_{idx}", width="stretch"):
                        with st.spinner("Sedang mengambil ulang gambar..."):
                            sukses, msh_nodata = capture_ulang_single(item)
                            if sukses:
                                for i, d in enumerate(st.session_state.hasil_capture):
                                    if d['path'] == item['path']:
                                        st.session_state.hasil_capture[i]['ada_no_data'] = msh_nodata
                                        break
                                if msh_nodata: st.error("❌ Masih No Data!")
                                else: st.success("✅ Berhasil terisi data!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Gagal capture ulang.")
                st.divider()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅ Lanjut Zip Semua File & Download", type="primary", width="stretch"):
            with st.spinner("Mengkompresi file ZIP..."):
                zip_buffer = zip_folder_to_memory(st.session_state.base_output_dir)
                st.session_state.zip_data = zip_buffer.getvalue() 
                st.session_state.zip_name = "Laporan_Reporting.zip" 
                st.session_state.status_aplikasi = "selesai"
                st.rerun()

    # --- STATE 5: SELESAI ---
    elif st.session_state.status_aplikasi == "selesai":
        st.title("✅ Tugas Selesai!")
        st.divider()
        st.success("Semua dashboard berhasil di-capture dan siap diunduh!")
        st.download_button("📥 Download Hasil Capture (ZIP)", data=st.session_state.zip_data, file_name=st.session_state.zip_name, mime="application/zip", width="stretch")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Kembali ke Beranda", width="stretch"):
            try: shutil.rmtree(st.session_state.temp_parent_dir, ignore_errors=True)
            except: pass
            
            st.session_state.status_aplikasi = "idle"
            st.rerun()
