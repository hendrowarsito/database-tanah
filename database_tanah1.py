import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import math

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Pangkalan Data Tanah — KJPP",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Pangkalan Data Tanah v2 — KJPP Suwendho Rinaldy dan Rekan"
    }
)

# ==========================================
# CUSTOM CSS — TEMA PROFESIONAL
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: #0f1923;
    border-right: 1px solid #1e2d3d;
}
[data-testid="stSidebar"] * {
    color: #c8d8e8 !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stFileUploader label,
[data-testid="stSidebar"] .stTextInput label {
    color: #7a9ab5 !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: #1a2838 !important;
    border: 1px solid #2a3f55 !important;
    border-radius: 8px !important;
    color: #c8d8e8 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1e2d3d !important;
}

/* ---- Tombol Utama ---- */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1a6b4a 0%, #0d4a32 100%);
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(26, 107, 74, 0.4) !important;
}

/* ---- Header Area ---- */
.main-header {
    background: linear-gradient(135deg, #0f1923 0%, #1a2e42 50%, #0f1923 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid #1e3348;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(26,107,74,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.main-header h1 {
    font-family: 'Lora', serif !important;
    font-size: 1.9rem !important;
    font-weight: 600 !important;
    color: #e8f4f0 !important;
    margin: 0 !important;
    letter-spacing: -0.01em !important;
}
.main-header p {
    color: #7a9ab5 !important;
    font-size: 0.85rem !important;
    margin: 0.4rem 0 0 0 !important;
    letter-spacing: 0.04em !important;
}
.header-badge {
    display: inline-block;
    background: rgba(26,107,74,0.2);
    border: 1px solid rgba(26,107,74,0.4);
    color: #4ecb8d !important;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 0.8rem;
}

/* ---- Metric Cards ---- */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #ffffff;
    border: 1px solid #e8ecf0;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.2s ease;
}
.metric-card:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.metric-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0;
    width: 100%; height: 3px;
}
.metric-card.green::after  { background: linear-gradient(90deg, #1a6b4a, #4ecb8d); }
.metric-card.blue::after   { background: linear-gradient(90deg, #1a5c8b, #4eaacb); }
.metric-card.amber::after  { background: linear-gradient(90deg, #9b6b1a, #cbaa4e); }
.metric-card.coral::after  { background: linear-gradient(90deg, #8b3a1a, #cb6e4e); }
.metric-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8a97a5;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1a2535;
    line-height: 1.2;
}
.metric-sub {
    font-size: 0.72rem;
    color: #9aabb8;
    margin-top: 0.2rem;
}

/* ---- Stat Cards (Tab Statistik) ---- */
.stat-section-title {
    font-family: 'Lora', serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #1a2535;
    margin: 1.5rem 0 0.8rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #e8ecf0;
}
.stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 1.2rem;
}
.stat-card {
    background: #fff;
    border: 1px solid #e8ecf0;
    border-radius: 14px;
    padding: 1.4rem 1.5rem;
    text-align: center;
}
.stat-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}
.stat-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8a97a5;
    margin-bottom: 0.6rem;
}
.stat-value {
    font-family: 'Lora', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: #1a2535;
    margin-bottom: 0.2rem;
}
.stat-value.green { color: #1a6b4a; }
.stat-value.coral { color: #a03a1a; }
.stat-value.blue  { color: #1a5c8b; }
.stat-sub {
    font-size: 0.72rem;
    color: #9aabb8;
}

/* ---- Bar Chart Horisontal ---- */
.bar-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}
.bar-label {
    font-size: 0.78rem;
    color: #4a5568;
    min-width: 130px;
    text-align: right;
    font-weight: 500;
}
.bar-track {
    flex: 1;
    height: 10px;
    background: #f0f4f8;
    border-radius: 5px;
    overflow: hidden;
}
.bar-fill {
    height: 100%;
    border-radius: 5px;
    background: linear-gradient(90deg, #1a6b4a, #4ecb8d);
    transition: width 0.5s ease;
}
.bar-val {
    font-size: 0.75rem;
    color: #4a5568;
    min-width: 110px;
    font-weight: 600;
}

/* ---- Result Badge ---- */
.result-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #f0f9f5;
    border: 1px solid #a8dfca;
    color: #1a6b4a;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 5px 14px;
    border-radius: 20px;
    margin-bottom: 1rem;
}

/* ---- Tabs ---- */
div[data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 2px solid #e8ecf0 !important;
    background: transparent !important;
}
div[data-baseweb="tab"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.6rem 1.2rem !important;
    color: #8a97a5 !important;
    border-radius: 0 !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    color: #1a6b4a !important;
    border-bottom: 2px solid #1a6b4a !important;
    background: transparent !important;
}

/* ---- Tabel ---- */
[data-testid="stDataFrame"] {
    border: 1px solid #e8ecf0 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ---- Info/Warning Box ---- */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* ---- Scrollbar ---- */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #f0f4f8; }
::-webkit-scrollbar-thumb { background: #c0d0dc; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def generate_streetview_url(lat, lon):
    return f"https://maps.google.com/maps?q=&layer=c&cbll={lat},{lon}"

@st.cache_data(show_spinner=False)
def load_data(file_bytes, file_name):
    """Cache berdasarkan konten file (bukan referensi objek)"""
    import io
    df = pd.read_excel(io.BytesIO(file_bytes))

    required_columns = ["Latitude", "Longitude", "Kota", "Tahun", "Nomor", "Harga_Tanah"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Kolom tidak ditemukan: **{', '.join(missing_cols)}**  \nPastikan file dihasilkan dari agregatordata v2.")
        st.stop()

    df["Latitude"]   = pd.to_numeric(df["Latitude"],   errors="coerce")
    df["Longitude"]  = pd.to_numeric(df["Longitude"],  errors="coerce")
    df["Harga_Tanah"] = pd.to_numeric(df["Harga_Tanah"], errors="coerce")
    return df

def format_currency(value):
    try:
        return f"Rp {float(value):,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"

def format_currency_short(value):
    try:
        v = float(value)
        if v >= 1_000_000_000:
            return f"Rp {v/1_000_000_000:.2f} M"
        elif v >= 1_000_000:
            return f"Rp {v/1_000_000:.1f} jt"
        else:
            return f"Rp {v:,.0f}".replace(",", ".")
    except Exception:
        return "Rp 0"

def bersihkan_tahun(val):
    try:
        return pd.to_numeric(str(val).replace(",", "").strip(), errors="coerce", downcast="integer")
    except Exception:
        return None

def get_color_by_year(year):
    try:
        year = int(year)
        if year >= 2025: return "green"
        elif year >= 2024: return "blue"
        elif year >= 2023: return "orange"
        else: return "red"
    except Exception:
        return "gray"

def build_bar_chart_html(data_series, label_col, value_col, max_val=None):
    """Membuat bar chart horizontal sederhana dalam HTML"""
    html = ""
    if data_series.empty:
        return "<p style='color:#9aabb8;font-size:0.8rem'>Tidak ada data</p>"
    if max_val is None:
        max_val = data_series[value_col].max()
    if max_val == 0:
        max_val = 1
    for _, row in data_series.iterrows():
        pct = (row[value_col] / max_val) * 100
        lbl = str(row[label_col])[:20]
        val_str = format_currency_short(row[value_col])
        html += f"""
        <div class="bar-row">
            <span class="bar-label">{lbl}</span>
            <div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%"></div></div>
            <span class="bar-val">{val_str}/m²</span>
        </div>"""
    return html

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem 0 0.5rem 0">
        <div style="font-family:'Lora',serif;font-size:1.1rem;font-weight:600;color:#e8f4f0;line-height:1.3">
            Pangkalan Data Tanah
        </div>
        <div style="font-size:0.72rem;color:#4ecb8d;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin-top:2px">
            KJPP Suwendho Rinaldy
        </div>
    </div>
    <hr style="border:none;border-top:1px solid #1e2d3d;margin:0.8rem 0">
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.7rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#4a6a85;margin-bottom:0.3rem">Sumber Data</p>', unsafe_allow_html=True)
    file = st.file_uploader("Unggah file Excel", type=["xlsx", "xls"], label_visibility="collapsed")

    st.markdown("<hr style='border:none;border-top:1px solid #1e2d3d;margin:1rem 0'>", unsafe_allow_html=True)

    if file and "last_file" in st.session_state and st.session_state["last_file"] != file.name:
        st.session_state["tampilkan"] = False
    if file:
        st.session_state["last_file"] = file.name

    if not file:
        st.markdown('<p style="font-size:0.78rem;color:#4a6a85;line-height:1.6">Unggah file Excel yang dihasilkan dari <b style="color:#7a9ab5">agregatordata v2</b> untuk memulai.</p>', unsafe_allow_html=True)
        st.stop()

    file_bytes = file.read()
    df = load_data(file_bytes, file.name)
    df["Tahun_Bersih"] = df["Tahun"].apply(bersihkan_tahun)

    st.markdown('<p style="font-size:0.7rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#4a6a85;margin-bottom:0.5rem">Filter Wilayah</p>', unsafe_allow_html=True)

    # ---- Helper: ambil opsi unik bersih dari kolom ----
    def get_options(series, all_label):
        opts = sorted([str(v) for v in series.dropna().unique() if str(v).strip() not in ("", "nan")])
        return [all_label] + opts

    # ---- FILTER 1: Propinsi (dari seluruh data) ----
    st.markdown('<p style="font-size:0.68rem;color:#4a6a85;margin:0 0 2px 0">Propinsi</p>', unsafe_allow_html=True)
    prov_options = get_options(df["Propinsi"], "Semua Propinsi")
    selected_prov = st.selectbox("Propinsi", prov_options, label_visibility="collapsed", key="sel_prov")

    # ---- Scope setelah filter Propinsi ----
    df_after_prov = df if selected_prov == "Semua Propinsi" else \
        df[df["Propinsi"].astype(str).str.strip().str.lower() == selected_prov.lower()]

    # ---- FILTER 2: Kota (cascading dari Propinsi) ----
    st.markdown('<p style="font-size:0.68rem;color:#4a6a85;margin:4px 0 2px 0">Kota / Kabupaten</p>', unsafe_allow_html=True)
    kota_options = get_options(df_after_prov["Kota"], "Semua Kota")
    # Reset Kota jika opsi yang dipilih sebelumnya tidak ada di list baru
    if st.session_state.get("sel_kota", "Semua Kota") not in kota_options:
        st.session_state["sel_kota"] = "Semua Kota"
    selected_city = st.selectbox("Kota", kota_options, label_visibility="collapsed", key="sel_kota")

    # ---- Scope setelah filter Kota ----
    df_after_kota = df_after_prov if selected_city == "Semua Kota" else \
        df_after_prov[df_after_prov["Kota"].astype(str).str.strip().str.lower() == selected_city.lower()]

    # ---- FILTER 3: Kecamatan (cascading dari Kota) ----
    st.markdown('<p style="font-size:0.68rem;color:#4a6a85;margin:4px 0 2px 0">Kecamatan</p>', unsafe_allow_html=True)
    kec_options = get_options(df_after_kota["Kecamatan"], "Semua Kecamatan")
    if st.session_state.get("sel_kec", "Semua Kecamatan") not in kec_options:
        st.session_state["sel_kec"] = "Semua Kecamatan"
    selected_kec = st.selectbox("Kecamatan", kec_options, label_visibility="collapsed", key="sel_kec")

    # ---- Scope setelah filter Kecamatan ----
    df_after_kec = df_after_kota if selected_kec == "Semua Kecamatan" else \
        df_after_kota[df_after_kota["Kecamatan"].astype(str).str.strip().str.lower() == selected_kec.lower()]

    # ---- FILTER 4: Kelurahan/Desa (cascading dari Kecamatan) ----
    st.markdown('<p style="font-size:0.68rem;color:#4a6a85;margin:4px 0 2px 0">Kelurahan / Desa</p>', unsafe_allow_html=True)
    kel_options = get_options(df_after_kec["Kelurahan"], "Semua Kelurahan")
    if st.session_state.get("sel_kel", "Semua Kelurahan") not in kel_options:
        st.session_state["sel_kel"] = "Semua Kelurahan"
    selected_kel = st.selectbox("Kelurahan", kel_options, label_visibility="collapsed", key="sel_kel")

    st.markdown("<hr style='border:none;border-top:1px solid #1e2d3d;margin:0.8rem 0'>", unsafe_allow_html=True)

    # ---- FILTER 5: Tahun (independen, tidak cascading) ----
    st.markdown('<p style="font-size:0.68rem;color:#4a6a85;margin:0 0 2px 0">Tahun Data</p>', unsafe_allow_html=True)
    available_years = sorted([int(y) for y in df["Tahun_Bersih"].dropna().unique()], reverse=True)
    selected_year = st.selectbox("Tahun", ["Semua Tahun"] + [str(t) for t in available_years],
                                 label_visibility="collapsed", key="sel_tahun")

    st.markdown("<hr style='border:none;border-top:1px solid #1e2d3d;margin:0.8rem 0'>", unsafe_allow_html=True)

    if "tampilkan" not in st.session_state:
        st.session_state["tampilkan"] = False

    if st.button("Tampilkan Data", type="primary"):
        st.session_state["tampilkan"] = True

    if not st.session_state["tampilkan"]:
        st.stop()

# ==========================================
# FILTERING
# ==========================================
filtered = df.copy()

# Propinsi
if selected_prov != "Semua Propinsi":
    filtered = filtered[filtered["Propinsi"].astype(str).str.strip().str.lower() == selected_prov.lower()]

# Kota
if selected_city != "Semua Kota":
    filtered = filtered[filtered["Kota"].astype(str).str.strip().str.lower() == selected_city.lower()]

# Kecamatan
if selected_kec != "Semua Kecamatan":
    filtered = filtered[filtered["Kecamatan"].astype(str).str.strip().str.lower() == selected_kec.lower()]

# Kelurahan / Desa
if selected_kel != "Semua Kelurahan":
    filtered = filtered[filtered["Kelurahan"].astype(str).str.strip().str.lower() == selected_kel.lower()]

# Tahun
if selected_year != "Semua Tahun":
    filtered = filtered[filtered["Tahun_Bersih"] == int(selected_year)]

valid_harga = filtered[filtered["Harga_Tanah"] > 0]["Harga_Tanah"]

# ==========================================
# HEADER
# ==========================================
# Bangun label lokasi dari filter yang aktif (dari yang paling luas ke paling sempit)
_loc_parts = []
if selected_prov  != "Semua Propinsi":  _loc_parts.append(selected_prov)
if selected_city  != "Semua Kota":      _loc_parts.append(selected_city)
if selected_kec   != "Semua Kecamatan": _loc_parts.append(f"Kec. {selected_kec}")
if selected_kel   != "Semua Kelurahan": _loc_parts.append(f"Kel. {selected_kel}")
location_label = " › ".join(_loc_parts) if _loc_parts else "Seluruh Wilayah"
year_label     = selected_year if selected_year != "Semua Tahun" else "Semua Tahun"

st.markdown(f"""
<div class="main-header">
    <div class="header-badge">Sistem Informasi Penilaian Properti</div>
    <h1>Pangkalan Data Tanah</h1>
    <p>KJPP Suwendho Rinaldy dan Rekan &nbsp;·&nbsp; {location_label} &nbsp;·&nbsp; {year_label}</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# METRIC CARDS
# ==========================================
total_data   = len(filtered)
total_kota   = filtered["Kota"].nunique()
valid_coords = filtered.dropna(subset=["Latitude", "Longitude"])
rata2        = valid_harga.mean() if not valid_harga.empty else 0

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card green">
        <div class="metric-label">Total Data</div>
        <div class="metric-value">{total_data:,}</div>
        <div class="metric-sub">record tersedia</div>
    </div>
    <div class="metric-card blue">
        <div class="metric-label">Kota / Kab.</div>
        <div class="metric-value">{total_kota}</div>
        <div class="metric-sub">wilayah tercakup</div>
    </div>
    <div class="metric-card amber">
        <div class="metric-label">Terplot di Peta</div>
        <div class="metric-value">{len(valid_coords)}</div>
        <div class="metric-sub">memiliki koordinat</div>
    </div>
    <div class="metric-card coral">
        <div class="metric-label">Rata-rata Harga</div>
        <div class="metric-value" style="font-size:1.1rem">{format_currency_short(rata2)}</div>
        <div class="metric-sub">per m² (data valid)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# TABS
# ==========================================
tab_peta, tab_tabel, tab_statistik = st.tabs(["🗺️  Peta Lokasi", "📋  Tabel Data", "📊  Statistik Harga"])

# --- TAB 1: PETA ---
with tab_peta:
    lat_c, lon_c = -2.548926, 118.0148634
    m = folium.Map(
        location=[lat_c, lon_c],
        zoom_start=5, min_zoom=4, max_zoom=18,
        prefer_canvas=True,
        tiles=None
    )

    folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        name='Voyager', attr='©OpenStreetMap ©CartoDB'
    ).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        name='Satellite', attr='Tiles © Esri'
    ).add_to(m)

    if not valid_coords.empty:
        min_lat = valid_coords["Latitude"].min()
        max_lat = valid_coords["Latitude"].max()
        min_lon = valid_coords["Longitude"].min()
        max_lon = valid_coords["Longitude"].max()
        m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

        for r in valid_coords.itertuples():
            tahun  = getattr(r, "Tahun", 0)
            nomor  = str(getattr(r, "Nomor", "")).strip()
            warna  = get_color_by_year(tahun)
            warna_teks = "red" if "obyek penilaian" in nomor.lower() else warna
            foto_link  = getattr(r, "Foto", "#")
            foto_link  = foto_link if pd.notna(foto_link) and str(foto_link) != "nan" else "#"

            popup   = f"<a href='{generate_streetview_url(r.Latitude, r.Longitude)}' target='_blank'>🔍 Lihat Street View</a>"
            tooltip = (
                f"<b>Data {r.Nomor}</b><br>"
                f"<b>{getattr(r, 'Kontak', '-')}</b> · {getattr(r, 'Telp', '-')}<br>"
                f"Tahun: {tahun} · Alamat: {getattr(r, 'Alamat', '-')}<br>"
                f"Kel. {getattr(r, 'Kelurahan', '-')}, Kec. {getattr(r, 'Kecamatan', '-')}, {getattr(r, 'Kota', '-')}<br>"
                f"Luas Tanah: {getattr(r, 'Luas_Tanah', 0)} m² | Bangunan: {getattr(r, 'Luas_Bangunan', 0)} m²<br>"
                f"<b>Harga: {format_currency(r.Harga_Tanah)}/m²</b>"
            )

            folium.Marker(
                location=[r.Latitude, r.Longitude],
                popup=popup, tooltip=tooltip,
                icon=folium.Icon(color=warna)
            ).add_to(m)

            folium.map.Marker(
                [r.Latitude, r.Longitude],
                icon=folium.DivIcon(
                    html=f"""
                    <div style='font-size:11px;color:{warna_teks};font-weight:700;
                                font-family:Plus Jakarta Sans,sans-serif;
                                text-shadow:1px 1px 0 white,-1px -1px 0 white,1px -1px 0 white,-1px 1px 0 white;
                                background:rgba(255,255,255,0.75);padding:2px 5px;
                                border-radius:5px;white-space:nowrap;
                                border:1px solid rgba(0,0,0,0.08)'>
                        {format_currency(r.Harga_Tanah)}/m²
                        <br><a href="{foto_link}" target="_blank"
                              style="color:{warna_teks};text-decoration:underline;font-size:10px">
                            #{nomor}
                        </a>
                    </div>"""
                )
            ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, use_container_width=True, height=680, returned_objects=[])

# --- TAB 2: TABEL ---
with tab_tabel:
    st.markdown(f'<div class="result-badge">✓ {len(filtered)} record ditampilkan</div>', unsafe_allow_html=True)

    display_df = filtered.drop(columns=["Tahun_Bersih"], errors="ignore")

    col_fmt = {}
    if "Harga_Total" in display_df.columns:
        col_fmt["Harga_Total"] = "{:,.0f}"
    if "Harga_Tanah" in display_df.columns:
        col_fmt["Harga_Tanah"] = "{:,.0f}"

    st.dataframe(
        display_df,
        use_container_width=True,
        height=520,
        column_config={
            "Harga_Total": st.column_config.NumberColumn("Harga Total (Rp)", format="%d"),
            "Harga_Tanah": st.column_config.NumberColumn("Harga Tanah /m² (Rp)", format="%d"),
            "Luas_Tanah":  st.column_config.NumberColumn("Luas Tanah (m²)", format="%.1f"),
            "Luas_Bangunan": st.column_config.NumberColumn("Luas Bangunan (m²)", format="%.1f"),
            "Latitude":    st.column_config.NumberColumn("Latitude", format="%.6f"),
            "Longitude":   st.column_config.NumberColumn("Longitude", format="%.6f"),
        }
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Download CSV",
        data=csv_data,
        file_name=f"data_tanah_{selected_city.replace(' ','_')}_{selected_year}.csv",
        mime="text/csv"
    )

# --- TAB 3: STATISTIK ---
with tab_statistik:
    if valid_harga.empty:
        st.info("Tidak ada data harga valid untuk filter yang dipilih.")
    else:
        harga_min  = valid_harga.min()
        harga_max  = valid_harga.max()
        harga_mean = valid_harga.mean()
        harga_med  = valid_harga.median()
        std_dev    = valid_harga.std()
        count_harga = len(valid_harga)

        # --- Kartu Harga Utama ---
        st.markdown('<div class="stat-section-title">Ringkasan Harga Tanah per m²</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-icon">📉</div>
                <div class="stat-label">Harga Terendah</div>
                <div class="stat-value coral">{format_currency_short(harga_min)}</div>
                <div class="stat-sub">per m²</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚖️</div>
                <div class="stat-label">Rata-rata</div>
                <div class="stat-value blue">{format_currency_short(harga_mean)}</div>
                <div class="stat-sub">mean · median {format_currency_short(harga_med)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📈</div>
                <div class="stat-label">Harga Tertinggi</div>
                <div class="stat-value green">{format_currency_short(harga_max)}</div>
                <div class="stat-sub">per m²</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- Kartu Metrik Tambahan ---
        spread_pct = ((harga_max - harga_min) / harga_mean * 100) if harga_mean > 0 else 0
        cv = (std_dev / harga_mean * 100) if harga_mean > 0 else 0

        st.markdown(f"""
        <div class="metric-grid" style="grid-template-columns:repeat(4,1fr)">
            <div class="metric-card blue">
                <div class="metric-label">Jumlah Data</div>
                <div class="metric-value">{count_harga:,}</div>
                <div class="metric-sub">data harga valid</div>
            </div>
            <div class="metric-card green">
                <div class="metric-label">Median</div>
                <div class="metric-value" style="font-size:1.1rem">{format_currency_short(harga_med)}</div>
                <div class="metric-sub">nilai tengah</div>
            </div>
            <div class="metric-card amber">
                <div class="metric-label">Std. Deviasi</div>
                <div class="metric-value" style="font-size:1.1rem">{format_currency_short(std_dev)}</div>
                <div class="metric-sub">dispersi harga</div>
            </div>
            <div class="metric-card coral">
                <div class="metric-label">Koef. Variasi</div>
                <div class="metric-value">{cv:.1f}%</div>
                <div class="metric-sub">homogenitas data</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- Bar Chart Rata-rata per Kota ---
        st.markdown('<div class="stat-section-title">Rata-rata Harga per Kota (Top 10)</div>', unsafe_allow_html=True)

        kota_stat = (
            filtered[filtered["Harga_Tanah"] > 0]
            .groupby("Kota")["Harga_Tanah"]
            .mean()
            .reset_index()
            .rename(columns={"Harga_Tanah": "Rata2_Harga"})
            .sort_values("Rata2_Harga", ascending=False)
            .head(10)
        )

        bar_html = build_bar_chart_html(kota_stat, "Kota", "Rata2_Harga")
        st.markdown(f'<div style="background:#fff;border:1px solid #e8ecf0;border-radius:14px;padding:1.4rem 1.5rem">{bar_html}</div>', unsafe_allow_html=True)

        # --- Bar Chart Rata-rata per Tahun ---
        st.markdown('<div class="stat-section-title">Tren Rata-rata Harga per Tahun</div>', unsafe_allow_html=True)

        tahun_stat = (
            filtered[filtered["Harga_Tanah"] > 0]
            .groupby("Tahun_Bersih")["Harga_Tanah"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"Tahun_Bersih": "Tahun", "mean": "Rata2_Harga", "count": "Jumlah"})
            .sort_values("Tahun")
        )

        bar_html2 = build_bar_chart_html(tahun_stat, "Tahun", "Rata2_Harga")
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.markdown(f'<div style="background:#fff;border:1px solid #e8ecf0;border-radius:14px;padding:1.4rem 1.5rem">{bar_html2}</div>', unsafe_allow_html=True)
        with col_b:
            st.markdown('<div style="background:#fff;border:1px solid #e8ecf0;border-radius:14px;padding:1.4rem 1.5rem">', unsafe_allow_html=True)
            st.markdown('<div class="stat-section-title" style="margin-top:0">Jumlah Data per Tahun</div>', unsafe_allow_html=True)
            tabel_tahun = tahun_stat[["Tahun", "Jumlah", "Rata2_Harga"]].copy()
            tabel_tahun["Rata2_Harga"] = tabel_tahun["Rata2_Harga"].apply(format_currency_short)
            st.dataframe(
                tabel_tahun.rename(columns={"Rata2_Harga": "Rata-rata /m²"}),
                use_container_width=True,
                hide_index=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Distribusi Rentang Harga ---
        st.markdown('<div class="stat-section-title">Distribusi Rentang Harga</div>', unsafe_allow_html=True)

        bins   = [0, 500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000, float('inf')]
        labels = ["< 500 rb", "500rb–1 jt", "1–2 jt", "2–5 jt", "5–10 jt", "> 10 jt"]
        dist   = pd.cut(valid_harga, bins=bins, labels=labels).value_counts().sort_index().reset_index()
        dist.columns = ["Rentang", "Jumlah"]
        dist["Persen"] = (dist["Jumlah"] / dist["Jumlah"].sum() * 100).round(1)

        dist_html = ""
        max_j = dist["Jumlah"].max() if dist["Jumlah"].max() > 0 else 1
        for _, row in dist.iterrows():
            pct_bar = (row["Jumlah"] / max_j) * 100
            dist_html += f"""
            <div class="bar-row">
                <span class="bar-label" style="min-width:90px">{row['Rentang']}</span>
                <div class="bar-track"><div class="bar-fill" style="width:{pct_bar:.1f}%;background:linear-gradient(90deg,#1a5c8b,#4eaacb)"></div></div>
                <span class="bar-val">{int(row['Jumlah'])} data &nbsp;<span style="color:#9aabb8">({row['Persen']}%)</span></span>
            </div>"""

        st.markdown(f'<div style="background:#fff;border:1px solid #e8ecf0;border-radius:14px;padding:1.4rem 1.5rem">{dist_html}</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:1rem;padding:0.8rem 1rem;background:#f0f9f5;border:1px solid #a8dfca;border-radius:10px;font-size:0.78rem;color:#2a6b4a;line-height:1.7">
        <b>Catatan metodologi:</b> Statistik dihitung dari data dengan <code>Harga_Tanah > 0</code>.
        Koefisien Variasi (KV) mengukur homogenitas: KV &lt; 15% = homogen, 15–30% = cukup homogen, &gt; 30% = heterogen.
        Nilai median digunakan sebagai indikator sentral yang lebih robust terhadap outlier.
        </div>
        """, unsafe_allow_html=True)
