import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# ==========================================
# AYARLAR
# ==========================================
# GOOGLE APPS SCRIPT WEB APP URL'NİZ (sonu /exec ile bitmeli)
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxWP8CUKFGuIUZ691zvHliyCxBjN-3lpfCO0BrjV1eaOk8YjgdV_Ym0A3iLyB33h7uUGg/exec"
# ==========================================

st.set_page_config(page_title="Eğitim Bilgisi Anketi", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0D1B3E; }
    .stApp, p, label, h1, h2, h3, h4, h5, h6, .stMarkdown { color: #FFFFFF !important; }
    div[data-baseweb="select"] > div, input { background-color: #F0F2F6 !important; color: #000000 !important; }
    hr { border-color: #4A5568 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("Eğitim Bilgisi Güncelleme Anketi")


@st.cache_data
def load_data():
    excel_path = None
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if 'Önlisans' in file and file.endswith('.xlsx') and not file.startswith('~'):
                excel_path = os.path.join(root, file)
                break
        if excel_path:
            break

    if excel_path:
        try:
            df = pd.read_excel(excel_path, sheet_name='Anket_Listesi', skiprows=2)
            if 'Üniversite' in df.columns and 'Program/Bölüm' in df.columns:
                grouped = df.groupby('Üniversite')['Program/Bölüm'].unique()
                return {str(k): sorted([str(x) for x in v]) for k, v in grouped.items()}
        except Exception:
            pass
    return None


uni_dept_map = load_data()

if uni_dept_map:
    universities = sorted(list(uni_dept_map.keys()))
else:
    st.warning("⚠️ Excel dosyası bulunamadı!")
    universities = ["Veri Bulunamadı"]
    uni_dept_map = {"Veri Bulunamadı": ["Veri Bulunamadı"]}

seviyeler = ["İlkokul", "Ortaokul", "Lise", "Ön Lisans", "Lisans", "Yüksek Lisans", "Doktora"]

# Üniversite/Bölüm seçiminin gerekli olduğu eğitim seviyeleri
yuksekogrenim_seviyeleri = ["Ön Lisans", "Lisans", "Yüksek Lisans", "Doktora"]

sicil = st.text_input("Sicil Numaranızı Giriniz (Zorunlu):", placeholder="Lütfen sicil numaranızı yazın...")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 1. Bölüm: Güncel Eğitim Bilgileriniz")

col1, col2 = st.columns(2)
with col1:
    seviye = st.selectbox("1. Eğitim Seviyesi", ["Seçiniz..."] + seviyeler)
with col2:
    durum = st.selectbox("2. Mezuniyet Durumu", ["Seçiniz...", "Mezun", "Devam Ediyor", "Terk"])

# Kurum ve Bölüm sadece Ön Lisans, Lisans, Yüksek Lisans ve Doktora seçildiğinde gösterilir
kurum = "Seçiniz..."
bolum = "Seçiniz..."
if seviye in yuksekogrenim_seviyeleri:
    kurum = st.selectbox("3. Kurum Adı (Listeden seçin veya yazarak arayın)", ["Seçiniz..."] + universities)
    bolum = st.selectbox(
        "4. Bölüm Adı (Listeden seçin veya yazarak arayın)",
        ["Seçiniz..."] + (uni_dept_map.get(kurum, []) if kurum not in ["Seçiniz...", "Veri Bulunamadı"] else [])
    )

# "Bölüm B - Son Mezun Olunan Eğitim Bilgisi" sadece Mezuniyet Durumu
# "Devam Ediyor" ya da "Terk" seçildiğinde gösterilir.
devam_terk_durumlari = ["Devam Ediyor", "Terk"]

son_seviye = "Seçiniz..."
son_kurum = "Seçiniz..."
son_bolum = "Seçiniz..."

if durum in devam_terk_durumlari:
    st.markdown("---")
    st.markdown("### 2. Bölüm: Son Tamamlanan Eğitim (Sadece Devam / Terk Seçenler İçin)")

    col3, col4 = st.columns(2)
    with col3:
        son_seviye = st.selectbox("5. Son Mezun Olunan Eğitim Seviyesi", ["Seçiniz..."] + seviyeler)
    with col4:
        if son_seviye in yuksekogrenim_seviyeleri:
            son_kurum = st.selectbox("6. Son Mezun Olunan Kurum Adı", ["Seçiniz..."] + universities)

    if son_seviye in yuksekogrenim_seviyeleri:
        son_bolum = st.selectbox(
            "7. Son Mezun Olunan Bölüm Adı",
            ["Seçiniz..."] + (uni_dept_map.get(son_kurum, []) if son_kurum not in ["Seçiniz...", "Veri Bulunamadı"] else [])
        )

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Kaydet", type="primary", use_container_width=True):
    if not sicil:
        st.error("❌ Lütfen Sicil Numaranızı giriniz.")
    elif durum == "Seçiniz..." or seviye == "Seçiniz...":
        st.error("❌ Lütfen Eğitim Seviyesi ve Mezuniyet Durumu alanlarını boş bırakmayınız.")
    elif durum in devam_terk_durumlari and son_seviye == "Seçiniz...":
        st.error("❌ Lütfen Son Mezun Olunan Eğitim Seviyesini seçiniz.")
    elif GOOGLE_WEBHOOK_URL == "BURAYA_LINKI_YAPISTIRIN":
        st.error("❌ Geliştirici Hatası: Lütfen koddaki GOOGLE_WEBHOOK_URL alanına Google linkini yapıştırın.")
    else:
        yeni_kayit = {
            "Kayıt Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Sicil Numarası": sicil,
            "1. Eğitim Seviyesi": seviye if seviye != "Seçiniz..." else "",
            "2. Mezuniyet Durumu": durum if durum != "Seçiniz..." else "",
            "3. Kurum Adı": kurum if kurum != "Seçiniz..." else "",
            "4. Bölüm Adı": bolum if bolum != "Seçiniz..." else "",
            "5. Son Mezuniyet Seviyesi": son_seviye if son_seviye != "Seçiniz..." else "",
            "6. Son Mezuniyet Kurumu": son_kurum if son_kurum != "Seçiniz..." else "",
            "7. Son Mezuniyet Bölümü": son_bolum if son_bolum != "Seçiniz..." else ""
        }

        try:
            with st.spinner("Veriler güvenli bir şekilde kaydediliyor..."):
                response = requests.post(GOOGLE_WEBHOOK_URL, json=yeni_kayit)

            # --- GEÇİCİ DEBUG SATIRLARI (sorun çözülünce silinebilir) ---
            st.write("Status code:", response.status_code)
            st.write("Response:", response.text)
            # --------------------------------------------------------------

            if response.status_code == 200:
                st.success(f"✅ Başarılı! {sicil} sicil numaralı çalışan için eğitim bilgileri merkeze iletildi.")
                st.balloons()
            else:
                st.error("❌ Veri gönderilirken sunucu hatası oluştu.")
        except Exception as e:
            st.error(f"❌ Bağlantı hatası: İnternet bağlantınızı kontrol edin. Detay: {e}")