import streamlit as st
import json
import os
import requests
from datetime import datetime
from docxtpl import DocxTemplate

# ================= KONFIGURASI =================
# Cuma butuh Token Telegram.
try:
    # PERBAIKAN: Panggil nama kuncinya ("TELEGRAM_TOKEN"), BUKAN isinya.
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
except:
    st.error("Setting TELEGRAM_TOKEN belum ada di secrets.toml!")
    st.stop()

ADMIN_ID = "416111259" 
TEMPLATE_FILENAME = "template_rekomendasi.docx" 

st.set_page_config(page_title="Suket Penelitian", page_icon="📝", layout="centered")

# CSS Styling
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stExpander { border-radius: 10px; }
    h1 { font-size: 1.8rem !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# ================= FUNGSI LOGIKA =================

def tentukan_tembusan_tiga(lokasi, jabatan_manual):
    lokasi_lower = lokasi.lower()
    list_sekolah = ['sd', 'mi ', 'smp', 'mts', 'sma', 'ma ', 'smk', 'man ']
    if any(keyword in lokasi_lower for keyword in list_sekolah):
        return f"Kepala Sekolah/Madrasah {lokasi}"
    if "ma'had" in lokasi_lower or "mahad" in lokasi_lower:
        return f"Mudir {lokasi}"
    return f"{jabatan_manual}"

def kirim_ke_admin_telegram(file_path, data_mhs):
    clean_token = TELEGRAM_TOKEN.strip()
    url = f"https://api.telegram.org/bot{clean_token}/sendDocument"
    
    wa = data_mhs['wa'].strip()
    wa_link = "62" + wa[1:] if wa.startswith("0") else (wa if wa.startswith("62") else "62" + wa)
    
    caption = (
        f"🚨 **PERMOHONAN IZIN PENELITIAN**\n"
        f"👤 {data_mhs['nama']} ({data_mhs['nim']})\n"
        f"🏢 Tujuan: {data_mhs['jabatan_tujuan']}\n"
        f"📍 Lokasi: {data_mhs['lokasi_tujuan']}\n"
        f"📱 WA: [{wa}](https://wa.me/{wa_link})\n\n"
        f"👉 Silakan TTE dan kirim balik ke mahasiswa."
    )
    
    try:
        with open(file_path, 'rb') as f:
            payload = {'chat_id': ADMIN_ID, 'caption': caption, 'parse_mode': 'Markdown'}
            resp = requests.post(url, data=payload, files={'document': f})
            if resp.status_code == 200: return True, "OK"
            return False, f"Telegram Error: {resp.text}"
    except Exception as e:
        return False, str(e)

# ================= UI APLIKASI =================
st.title("📝 Surat Izin Penelitian")
st.caption("Fakultas Tarbiyah & Ilmu Keguruan")

if 'data' not in st.session_state: 
    st.session_state.data = {
        'nama': '', 'nim': '', 'sem': '', 'prodi': '', 'judul': '', 'wa': '',
        'jabatan_tujuan': '', 'lokasi_tujuan': ''
    }

# 1. INPUT WA
st.info("📱 **Kontak Mahasiswa**")
st.session_state.data['wa'] = st.text_input("Nomor WhatsApp (Wajib)", st.session_state.data['wa'])

# 2. FORM ISIAN DATA (Manual)
st.markdown("---")
st.info("📝 **Data Surat**")
d = st.session_state.data

# Input Data Identitas
d['nama'] = st.text_input("Nama Mahasiswa", d['nama'])
c1, c2 = st.columns(2)
with c1: d['nim'] = st.text_input("NIM", d['nim'])
with c2: d['sem'] = st.text_input("Semester (Contoh: VII (Tujuh))", d['sem'])
d['prodi'] = st.text_input("Program Studi", d.get('prodi', 'Pendidikan Bahasa Arab'))
d['judul'] = st.text_area("Judul Penelitian", d['judul'])

st.markdown("---")
st.write("📍 **Tujuan Surat**")
d['jabatan_tujuan'] = st.text_input("Kepada Yth (Jabatan Lengkap)", d['jabatan_tujuan'], 
                                    placeholder="Contoh: Kepala Sekolah MAN 1 Ternate")
d['lokasi_tujuan'] = st.text_input("Nama Tempat / Lokasi", d['lokasi_tujuan'], 
                                   placeholder="Contoh: MAN 1 Ternate")

# 3. EKSEKUSI
st.markdown("---")
if st.button("🚀 KIRIM KE ADMIN", type="primary"):
    # Cek kelengkapan data
    if not d['wa'] or not d['nama'] or not d['nim'] or not d['judul'] or not d['jabatan_tujuan']:
        st.warning("⚠️ Mohon lengkapi semua data di atas!")
    else:
        with st.spinner("Memproses Surat..."):
            try:
                now = datetime.now()
                bln_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
                
                # Logika Tembusan
                txt_tembusan_3 = tentukan_tembusan_tiga(d['lokasi_tujuan'], d['jabatan_tujuan'])

                ctx = {
                    'nama': d['nama'], 
                    'nim': d['nim'], 
                    'semester': d['sem'],
                    'prodi': d['prodi'], 
                    'judul': d['judul'],
                    'jabatan_tujuan': d['jabatan_tujuan'],
                    'lokasi_tujuan': d['lokasi_tujuan'],
                    'tanggal_surat': f"{now.day} {bln_indo[now.month-1]} {now.year}",
                    'bln_angka': str(now.month),
                    'thn': str(now.year),
                    'tembusan_tiga': txt_tembusan_3
                }
                
                doc = DocxTemplate(TEMPLATE_FILENAME)
                doc.render(ctx)
                # Ambil nama depan saja & bersihkan simbol aneh
                nama_depan = d['nama'].strip().split()[0]
                nama_clean = "".join(x for x in nama_depan if x.isalnum())
                # Jadikan nama file
                out = f"Rekom_{nama_clean}.docx"
                doc.save(out)
                
                sukses, msg = kirim_ke_admin_telegram(out, d)
                if sukses:
                    st.balloons()
                    st.success("✅ BERHASIL! Surat permohonan sudah dikirim ke Admin.")
                else:
                    st.error(f"❌ Gagal Kirim Telegram: {msg}")
            except Exception as e:
                st.error(f"System Error: {e}")
