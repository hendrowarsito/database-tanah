"""
scraper_properti.py — Prototipe Web Scraper Properti
Sumber  : rumah123.com (halaman listing tanah)
Deploy  : Streamlit Cloud (GitHub)
Versi   : 1.1 — Fix ModuleNotFoundError httpx

Strategi parsing:
  Rumah123 adalah Next.js app. Data listing tersimpan di tag <script id="__NEXT_DATA__">
  dalam format JSON — jauh lebih andal dari CSS selector yang bisa berubah kapan saja.
  Pendekatan: requests (request ringan) → BeautifulSoup cari __NEXT_DATA__ → parse JSON.

Dependencies (requirements.txt) — WAJIB ada di root repo GitHub:
  streamlit>=1.28.0
  requests>=2.31.0
  beautifulsoup4>=4.12.0
  lxml>=4.9.0
  pandas>=2.0.0
  openpyxl>=3.1.0
  xlrd>=2.0.0
"""

import streamlit as st
import json
import re
import time
import random
import pandas as pd
import io
from datetime import datetime
from bs4 import BeautifulSoup

# HTTP client — requests adalah standar universal, pasti tersedia di semua environment.
# Tidak menggunakan httpx karena sering gagal resolve di Streamlit Cloud akibat
# dependency conflict dengan versi streamlit yang sudah terinstall.
try:
    import requests as _http_lib
    _HTTP_BACKEND = "requests"
except ImportError:
    _http_lib = None
    _HTTP_BACKEND = "none"

# ==========================================
# KONFIGURASI
# ==========================================

BASE_URL = "https://www.rumah123.com"

# Pola URL pencarian tanah per kota
# Format: /jual/{slug-kota}/tanah/?page={n}
# Kecamatan ditambahkan via parameter ?keyword=
URL_TEMPLATE = "{base}/jual/{kota_slug}/tanah/"

# Daftar kota beserta slug URL-nya
# Slug bisa dicek dari URL di browser saat browsing rumah123
KOTA_SLUG = {
    "Bandung":          "bandung",
    "Kab. Bandung":     "kabupaten-bandung",
    "Jakarta Selatan":  "jakarta-selatan",
    "Jakarta Barat":    "jakarta-barat",
    "Jakarta Timur":    "jakarta-timur",
    "Jakarta Utara":    "jakarta-utara",
    "Jakarta Pusat":    "jakarta-pusat",
    "Surabaya":         "surabaya",
    "Semarang":         "semarang",
    "Yogyakarta":       "yogyakarta",
    "Medan":            "medan",
    "Makassar":         "makassar",
    "Depok":            "depok",
    "Bekasi":           "bekasi",
    "Tangerang":        "tangerang",
    "Bogor":            "bogor",
    "Malang":           "malang",
    "Palembang":        "palembang",
    "Balikpapan":       "balikpapan",
    "Denpasar":         "denpasar",
}

# Header HTTP lengkap — menyerupai Chrome nyata di Windows sedetail mungkin.
# Rumah123 memeriksa kombinasi header, bukan hanya User-Agent.
# Urutan header juga penting — browser selalu mengirim dalam urutan tertentu.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;"
        "q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language":  "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding":  "gzip, deflate, br",
    "Connection":       "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest":   "document",
    "Sec-Fetch-Mode":   "navigate",
    "Sec-Fetch-Site":   "none",
    "Sec-Fetch-User":   "?1",
    "Sec-Ch-Ua":        '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Cache-Control":    "max-age=0",
    "Referer":          "https://www.google.co.id/",
}

# ScraperAPI — proxy residensial gratis 1.000 req/bulan
# Daftar di: https://www.scraperapi.com (pilih Free plan)
# Cara kerja: request dikirim ke api.scraperapi.com dengan URL target sebagai parameter,
# ScraperAPI meneruskan dari IP residential yang tidak dikenali sebagai bot.
SCRAPERAPI_ENDPOINT = "https://api.scraperapi.com"

def build_fetch_url(target_url: str, api_key: str) -> tuple[str, dict]:
    """
    Jika api_key diisi  → gunakan ScraperAPI sebagai proxy.
                          Menambahkan parameter render=false (HTML statis, lebih cepat)
                          dan country_code=id (IP Indonesia, relevan untuk rumah123).
    Jika api_key kosong → request langsung ke target (mungkin 403 dari cloud).

    Mengembalikan (url_final, extra_params) yang siap dipakai requests.get().
    """
    if api_key and api_key.strip():
        params = {
            "api_key":     api_key.strip(),
            "url":         target_url,
            "render":      "false",   # false = lebih cepat, cukup untuk SSR/Next.js
            "country_code": "id",     # IP dari Indonesia
            "keep_headers": "true",   # teruskan HEADERS kita ke target
        }
        return SCRAPERAPI_ENDPOINT, params
    else:
        return target_url, {}

# Kolom output — didesain kompatibel dengan Pangkalandata8
KOLOM_OUTPUT = [
    "Timestamp", "Nomor", "Tahun", "URL_Sumber",
    "Judul_Iklan", "Alamat", "Kecamatan", "Kota", "Propinsi",
    "Luas_Tanah", "Luas_Bangunan",
    "Harga_Total", "Harga_Tanah",
    "Peruntukan", "Bukti_Kepemilikan",
    "Latitude", "Longitude",
    "Kontak", "Agen",
    "Foto_URL", "Deskripsi",
]

# ==========================================
# HELPER: PARSING HARGA
# ==========================================

def parse_harga(text):
    """
    Mengkonversi string harga rumah123 ke integer.
    Contoh input: 'Rp 1,5 Miliar', 'Rp 500 Juta', 'Rp 750.000.000'
    """
    if not text:
        return 0
    text = str(text).lower().strip()
    text = text.replace("rp", "").replace(" ", "").strip()
    try:
        if "miliar" in text or "m" == text[-1]:
            angka = float(re.sub(r"[^0-9,.]", "", text).replace(",", "."))
            return int(angka * 1_000_000_000)
        elif "juta" in text:
            angka = float(re.sub(r"[^0-9,.]", "", text).replace(",", "."))
            return int(angka * 1_000_000)
        else:
            clean = re.sub(r"[^0-9]", "", text)
            return int(clean) if clean else 0
    except Exception:
        return 0


def parse_luas(text):
    """
    Mengambil angka luas dari string seperti 'LT: 250 m²' atau '250 m²'.
    """
    if not text:
        return 0
    try:
        numbers = re.findall(r"[\d,.]+", str(text))
        if numbers:
            return float(numbers[0].replace(",", "."))
    except Exception:
        pass
    return 0


def hitung_harga_per_m2(harga_total, luas_tanah):
    """Hitung indikasi harga per m²."""
    try:
        if luas_tanah and luas_tanah > 0:
            return round(harga_total / luas_tanah)
    except Exception:
        pass
    return 0


# ==========================================
# CORE: FETCH HALAMAN
# ==========================================

def fetch_page(url, api_key="", timeout=30):
    """
    Mengambil HTML halaman. Mendukung dua mode:
    - Direct     : request langsung ke rumah123 (mungkin 403 dari Streamlit Cloud)
    - ScraperAPI : request melalui proxy residensial (bypass 403)

    Mode ditentukan otomatis berdasarkan ada/tidaknya api_key.
    """
    if _http_lib is None:
        return None, "Library HTTP tidak tersedia — pastikan 'requests' ada di requirements.txt"

    fetch_url, extra_params = build_fetch_url(url, api_key)
    mode = "ScraperAPI" if extra_params else "Direct"

    try:
        session = _http_lib.Session()
        session.headers.update(HEADERS)
        session.cookies.set("consent",      "true",        domain=".rumah123.com")
        session.cookies.set("cookieconsent", "accepted",   domain=".rumah123.com")

        resp = session.get(
            fetch_url,
            params=extra_params if extra_params else None,
            timeout=timeout,
            allow_redirects=True,
        )

        if resp.status_code == 200:
            return resp.text, 200
        elif resp.status_code == 403:
            if mode == "Direct":
                return None, (
                    "403 — IP Streamlit Cloud diblokir rumah123. "
                    "Masukkan ScraperAPI Key di sidebar untuk bypass."
                )
            else:
                return None, "403 — ScraperAPI juga diblokir (coba ganti country_code atau cek kuota key)"
        elif resp.status_code == 401:
            return None, "401 — ScraperAPI Key tidak valid atau kuota habis"
        elif resp.status_code == 404:
            return None, "404 — Halaman tidak ditemukan, cek slug kota"
        elif resp.status_code == 429:
            return None, "429 — Terlalu banyak request, tambah jeda dan coba lagi"
        else:
            return None, f"HTTP {resp.status_code} via {mode}"

    except _http_lib.exceptions.Timeout:
        return None, f"Timeout via {mode} — coba naikkan batas waktu"
    except _http_lib.exceptions.ConnectionError:
        return None, f"Connection error via {mode}"
    except Exception as e:
        return None, f"Error tidak terduga via {mode}: {str(e)}"


# ==========================================
# CORE: EKSTRAK DATA DARI __NEXT_DATA__
# ==========================================

def extract_next_data(html):
    """
    Mengambil JSON dari tag <script id="__NEXT_DATA__">.
    Ini pendekatan paling andal untuk Next.js sites karena:
    - Data sudah terstruktur (tidak perlu parsing HTML fragile)
    - Tidak terpengaruh perubahan CSS class
    - Tersedia selama rumah123 menggunakan Next.js (sudah bertahun-tahun)
    """
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if not tag or not tag.string:
        return None
    try:
        return json.loads(tag.string)
    except json.JSONDecodeError:
        return None


def find_listings_in_json(data, depth=0, max_depth=8):
    """
    Rekursif mencari array listing di dalam struktur JSON Next.js.
    Rumah123 menyimpan listings di path yang bisa berubah antar halaman,
    sehingga pendekatan rekursif lebih tahan perubahan struktur.

    Indikator array listing: list berisi dict yang memiliki key 'price' atau 'id'
    dengan panjang > 0.
    """
    if depth > max_depth or data is None:
        return None

    if isinstance(data, list) and len(data) > 0:
        # Cek apakah ini array listing berdasarkan key yang ada
        sample = data[0] if data else {}
        if isinstance(sample, dict):
            keys = set(sample.keys())
            # Signature key listing rumah123
            listing_keys = {"price", "title", "id", "address", "attributes"}
            if len(listing_keys & keys) >= 2:
                return data

    if isinstance(data, dict):
        # Prioritas: cek key yang kemungkinan besar berisi listings
        priority_keys = ["listings", "properties", "data", "results",
                         "pageProps", "initialData", "listingData"]
        for key in priority_keys:
            if key in data:
                result = find_listings_in_json(data[key], depth + 1, max_depth)
                if result:
                    return result
        # Fallback: cek semua key
        for key, val in data.items():
            if key not in priority_keys:
                result = find_listings_in_json(val, depth + 1, max_depth)
                if result:
                    return result

    return None


def parse_single_listing(item, kota_filter, idx):
    """
    Memetakan satu dict listing dari JSON ke format kolom Pangkalandata.
    Menggunakan .get() di semua level agar tidak crash jika field tidak ada.
    """
    try:
        # --- ID dan URL ---
        listing_id = item.get("id", "")
        url_path   = item.get("url", "") or item.get("shareUrl", "")
        if url_path and not url_path.startswith("http"):
            url_path = BASE_URL + url_path
        if not url_path and listing_id:
            url_path = f"{BASE_URL}/properti/{listing_id}.html"

        # --- Judul ---
        judul = item.get("title", "") or item.get("name", "")

        # --- Harga ---
        price_raw = item.get("price", {})
        if isinstance(price_raw, dict):
            harga_text = price_raw.get("text", "") or str(price_raw.get("value", 0))
        else:
            harga_text = str(price_raw)
        harga_total = parse_harga(harga_text)

        # --- Atribut properti (luas, sertifikat, dll) ---
        attrs = item.get("attributes", {}) or {}
        if isinstance(attrs, list):
            # Beberapa versi menyimpan sebagai list of {label, value}
            attrs_dict = {a.get("label", "").lower(): a.get("value", "") for a in attrs}
        else:
            attrs_dict = {k.lower(): v for k, v in attrs.items()}

        # Luas tanah
        luas_tnh_raw = (
            attrs_dict.get("land size", 0) or
            attrs_dict.get("landsize", 0) or
            attrs_dict.get("luas tanah", 0) or
            item.get("landSize", 0) or
            item.get("land_size", 0)
        )
        luas_tanah = parse_luas(luas_tnh_raw)

        # Luas bangunan
        luas_bgn_raw = (
            attrs_dict.get("building size", 0) or
            attrs_dict.get("buildingsize", 0) or
            attrs_dict.get("luas bangunan", 0) or
            item.get("buildingSize", 0) or
            item.get("building_size", 0)
        )
        luas_bgn = parse_luas(luas_bgn_raw)

        # Sertifikat / legalitas
        sertifikat = (
            attrs_dict.get("certificate", "") or
            attrs_dict.get("sertifikat", "") or
            attrs_dict.get("ownership", "") or
            item.get("certificate", "")
        )

        # --- Lokasi ---
        address = item.get("address", {}) or {}
        if isinstance(address, str):
            alamat_str  = address
            kecamatan   = ""
            kota_str    = kota_filter
            propinsi    = ""
        else:
            alamat_str  = address.get("street", "") or address.get("text", "")
            kecamatan   = address.get("district", "") or address.get("subdistrict", "")
            kota_str    = address.get("city", "") or kota_filter
            propinsi    = address.get("province", "") or address.get("state", "")

        # Fallback: kadang lokasi ada di key terpisah
        if not kota_str:
            kota_str = item.get("city", "") or kota_filter
        if not kecamatan:
            kecamatan = item.get("district", "")

        # --- Koordinat ---
        coordinate = item.get("coordinate", {}) or item.get("location", {}) or {}
        if isinstance(coordinate, dict):
            lat = coordinate.get("latitude", coordinate.get("lat", None))
            lon = coordinate.get("longitude", coordinate.get("lng", coordinate.get("lon", None)))
        else:
            lat, lon = None, None

        # --- Kontak & Agen ---
        agent = item.get("agent", {}) or item.get("contact", {}) or {}
        if isinstance(agent, dict):
            nama_agen = agent.get("name", "") or agent.get("fullName", "")
            telp_agen = agent.get("phone", "") or agent.get("phoneNumber", "")
        else:
            nama_agen = str(agent)
            telp_agen = ""

        # --- Foto ---
        photos = item.get("photos", []) or item.get("images", []) or []
        foto_url = ""
        if photos and isinstance(photos, list):
            first = photos[0]
            if isinstance(first, dict):
                foto_url = first.get("url", first.get("mediaUrl", first.get("src", "")))
            elif isinstance(first, str):
                foto_url = first

        # --- Deskripsi ---
        deskripsi = item.get("description", "") or item.get("shortDescription", "")
        if deskripsi:
            deskripsi = deskripsi[:300]  # Batasi panjang

        # --- Harga per m² ---
        harga_per_m2 = hitung_harga_per_m2(harga_total, luas_tanah)

        # --- Tahun dari tanggal listing ---
        listed_at = item.get("listingDate", "") or item.get("createdAt", "")
        try:
            tahun = int(str(listed_at)[:4]) if listed_at else datetime.now().year
            if tahun < 2000 or tahun > 2030:
                tahun = datetime.now().year
        except Exception:
            tahun = datetime.now().year

        # --- Nomor unik ---
        nomor = f"R123-{str(listing_id)[:8] or str(idx).zfill(4)}"

        return {
            "Timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Nomor":            nomor,
            "Tahun":            tahun,
            "URL_Sumber":       url_path,
            "Judul_Iklan":      str(judul).strip(),
            "Alamat":           str(alamat_str).strip(),
            "Kecamatan":        str(kecamatan).strip(),
            "Kota":             str(kota_str).strip(),
            "Propinsi":         str(propinsi).strip(),
            "Luas_Tanah":       luas_tanah,
            "Luas_Bangunan":    luas_bgn,
            "Harga_Total":      harga_total,
            "Harga_Tanah":      harga_per_m2,
            "Peruntukan":       "",
            "Bukti_Kepemilikan": str(sertifikat).strip(),
            "Latitude":         lat,
            "Longitude":        lon,
            "Kontak":           str(telp_agen).strip(),
            "Agen":             str(nama_agen).strip(),
            "Foto_URL":         str(foto_url).strip(),
            "Deskripsi":        str(deskripsi).strip(),
        }

    except Exception as e:
        return None


# ==========================================
# CORE: SCRAPE SATU HALAMAN
# ==========================================

def scrape_satu_halaman(kota_nama, kecamatan_filter="", page=1,
                        delay_min=3, delay_max=7, api_key=""):
    """
    Mengambil data listing dari satu halaman pencarian.
    Mengembalikan (list_records, status_msg, raw_debug).

    delay_min/max: jeda detik sebelum request (rate limiting).
    """
    slug = KOTA_SLUG.get(kota_nama, kota_nama.lower().replace(" ", "-"))
    url  = URL_TEMPLATE.format(base=BASE_URL, kota_slug=slug)

    params = {"page": page}
    if kecamatan_filter.strip():
        params["keyword"] = kecamatan_filter.strip()

    # Bangun URL dengan parameter
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    full_url  = f"{url}?{param_str}"

    # Jeda sebelum request
    if delay_min > 0:
        jeda = random.uniform(delay_min, delay_max)
        time.sleep(jeda)

    html, status = fetch_page(full_url, api_key=api_key)

    if html is None:
        return [], f"Gagal fetch: {status}", {"url": full_url, "error": status}

    # Parse __NEXT_DATA__
    next_data = extract_next_data(html)
    if next_data is None:
        # Fallback: cek apakah ada JSON inline lain
        debug = {
            "url": full_url,
            "html_length": len(html),
            "has_next_data": False,
            "note": (
                "__NEXT_DATA__ tidak ditemukan. Kemungkinan: "
                "(1) halaman di-render via CSR bukan SSR — perlu Playwright, "
                "(2) struktur halaman berubah, "
                "(3) IP diblokir sementara."
            )
        }
        return [], "Parsing gagal: __NEXT_DATA__ tidak ditemukan", debug

    listings_raw = find_listings_in_json(next_data)
    debug = {
        "url": full_url,
        "html_length": len(html),
        "has_next_data": True,
        "listings_found": len(listings_raw) if listings_raw else 0,
        "next_data_keys": list(next_data.keys()) if isinstance(next_data, dict) else [],
    }

    if not listings_raw:
        debug["note"] = (
            "__NEXT_DATA__ ada tapi listings tidak ditemukan. "
            "Kemungkinan struktur JSON berubah. "
            "Cek debug_json untuk inspeksi manual."
        )
        # Simpan sampel JSON untuk debugging
        debug["sample_json"] = str(next_data)[:2000]
        return [], "Parsing gagal: listing tidak ditemukan di JSON", debug

    records = []
    for idx, item in enumerate(listings_raw):
        parsed = parse_single_listing(item, kota_nama, idx + 1)
        if parsed and parsed.get("Luas_Tanah", 0) > 0:
            records.append(parsed)

    status_msg = f"OK — {len(records)} listing valid dari {len(listings_raw)} item JSON"
    return records, status_msg, debug


# ==========================================
# DEDUPLICATION
# ==========================================

def cek_dan_hapus_duplikat(df_baru, df_existing):
    """
    Menghapus baris di df_baru yang URL_Sumber-nya sudah ada di df_existing.
    Menggunakan URL_Sumber sebagai kunci karena ID listing rumah123 bersifat permanen.
    """
    if df_existing.empty or "URL_Sumber" not in df_existing.columns:
        return df_baru, 0

    existing_urls = set(df_existing["URL_Sumber"].dropna().str.strip())
    mask_baru     = ~df_baru["URL_Sumber"].str.strip().isin(existing_urls)
    df_filtered   = df_baru[mask_baru].copy()
    jumlah_duplikat = len(df_baru) - len(df_filtered)

    return df_filtered, jumlah_duplikat


def to_excel_bytes(df):
    """Konversi DataFrame ke bytes Excel untuk st.download_button."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data Scraping")
    buf.seek(0)
    return buf.getvalue()


# ==========================================
# STREAMLIT UI
# ==========================================

st.set_page_config(
    page_title="Scraper Properti — KJPP",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Lora:wght@600&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

[data-testid="stSidebar"] {
    background: #0f1923;
    border-right: 1px solid #1e2d3d;
}
[data-testid="stSidebar"] * { color: #c8d8e8 !important; }
[data-testid="stSidebar"] hr { border-color: #1e2d3d !important; }

div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1a6b4a 0%, #0d4a32 100%);
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    width: 100% !important; padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(26,107,74,0.4) !important;
}

.page-header {
    background: linear-gradient(135deg, #0f1923 0%, #1a2e42 50%, #0f1923 100%);
    border-radius: 16px; padding: 1.8rem 2.2rem; margin-bottom: 1.5rem;
    border: 1px solid #1e3348;
}
.page-header h1 {
    font-family: 'Lora', serif !important; font-size: 1.7rem !important;
    color: #e8f4f0 !important; margin: 0 !important;
}
.page-header p { color: #7a9ab5 !important; font-size: 0.82rem !important; margin: 0.3rem 0 0 !important; }
.badge {
    display: inline-block; background: rgba(26,107,74,0.2);
    border: 1px solid rgba(26,107,74,0.4); color: #4ecb8d !important;
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; padding: 2px 9px; border-radius: 20px; margin-bottom: 0.7rem;
}
.stat-row {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 12px; margin-bottom: 1.2rem;
}
.stat-box {
    background: #fff; border: 1px solid #e8ecf0;
    border-radius: 12px; padding: 1rem 1.2rem;
}
.stat-box .lbl { font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: #8a97a5; margin-bottom: 0.3rem; }
.stat-box .val { font-size: 1.4rem; font-weight: 700; color: #1a2535; }
.stat-box .sub { font-size: 0.7rem; color: #9aabb8; margin-top: 0.1rem; }
.stat-box.g::after { content:''; display:block; height:3px; margin-top:0.8rem;
    border-radius:2px; background:linear-gradient(90deg,#1a6b4a,#4ecb8d); }
.stat-box.b::after { content:''; display:block; height:3px; margin-top:0.8rem;
    border-radius:2px; background:linear-gradient(90deg,#1a5c8b,#4eaacb); }
.stat-box.a::after { content:''; display:block; height:3px; margin-top:0.8rem;
    border-radius:2px; background:linear-gradient(90deg,#9b6b1a,#cbaa4e); }
.stat-box.r::after { content:''; display:block; height:3px; margin-top:0.8rem;
    border-radius:2px; background:linear-gradient(90deg,#8b3a1a,#cb6e4e); }
.warn-box {
    background: #fffbeb; border: 1px solid #f6d860;
    border-radius: 10px; padding: 0.9rem 1.1rem;
    font-size: 0.8rem; color: #7a5c0a; margin-bottom: 1rem;
}
.ok-box {
    background: #f0f9f5; border: 1px solid #a8dfca;
    border-radius: 10px; padding: 0.9rem 1.1rem;
    font-size: 0.8rem; color: #1a6b4a; margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 0.5rem">
        <div style="font-family:'Lora',serif;font-size:1rem;font-weight:600;color:#e8f4f0">
            Scraper Properti
        </div>
        <div style="font-size:0.7rem;color:#4ecb8d;font-weight:600;letter-spacing:0.08em;
                    text-transform:uppercase;margin-top:2px">
            KJPP Suwendho Rinaldy
        </div>
    </div>
    <hr style="border:none;border-top:1px solid #1e2d3d;margin:0.7rem 0">
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.68rem;font-weight:600;letter-spacing:0.1em;'
                'text-transform:uppercase;color:#4a6a85;margin:0 0 4px 0">Sumber Data</p>',
                unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.78rem;color:#7a9ab5;margin:0 0 0.8rem 0">'
                'rumah123.com — Tanah Dijual</p>', unsafe_allow_html=True)

    st.markdown('<hr style="border:none;border-top:1px solid #1e2d3d;margin:0.7rem 0">',
                unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.68rem;font-weight:600;letter-spacing:0.1em;'
                'text-transform:uppercase;color:#4a6a85;margin:0 0 6px 0">Filter Lokasi</p>',
                unsafe_allow_html=True)

    kota_pilihan = st.selectbox(
        "Kota", list(KOTA_SLUG.keys()),
        label_visibility="collapsed",
        help="Pilih kota target scraping"
    )

    kecamatan_input = st.text_input(
        "Kecamatan (opsional)",
        placeholder="Cth: Coblong, Buah Batu",
        label_visibility="collapsed",
        help="Isi untuk mempersempit hasil ke kecamatan tertentu"
    )

    st.markdown('<hr style="border:none;border-top:1px solid #1e2d3d;margin:0.7rem 0">',
                unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.68rem;font-weight:600;letter-spacing:0.1em;'
                'text-transform:uppercase;color:#4a6a85;margin:0 0 6px 0">Opsi Scraping</p>',
                unsafe_allow_html=True)

    jeda_min = st.slider("Jeda min (detik)", 1, 10, 3,
                         help="Jeda minimum antar request — hindari terlalu cepat")
    jeda_max = st.slider("Jeda max (detik)", jeda_min, 15, 7)

    st.markdown('<hr style="border:none;border-top:1px solid #1e2d3d;margin:0.7rem 0">',
                unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.68rem;font-weight:600;letter-spacing:0.1em;'
                'text-transform:uppercase;color:#4a6a85;margin:0 0 6px 0">'
                'Cek Duplikat (Opsional)</p>', unsafe_allow_html=True)
    file_existing = st.file_uploader(
        "Upload Master Excel existing",
        type=["xlsx", "xls"],
        label_visibility="collapsed",
        help="Upload file hasil scraping sebelumnya untuk cek duplikat"
    )

    st.markdown('<hr style="border:none;border-top:1px solid #1e2d3d;margin:0.7rem 0">',
                unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:0.68rem;font-weight:600;letter-spacing:0.1em;'
        'text-transform:uppercase;color:#4a6a85;margin:0 0 4px 0">'
        'ScraperAPI Key</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="font-size:0.72rem;color:#4a6a85;line-height:1.5;margin:0 0 6px 0">'
        'Wajib diisi jika dijalankan dari Streamlit Cloud. '
        'Daftar gratis di <b style="color:#7a9ab5">scraperapi.com</b> '
        '(1.000 req/bulan).</p>',
        unsafe_allow_html=True
    )
    scraperapi_key = st.text_input(
        "ScraperAPI Key",
        placeholder="Paste API key di sini...",
        type="password",
        label_visibility="collapsed",
        help="Tanpa key: mungkin 403 dari cloud. Dengan key: bypass anti-bot rumah123."
    )

    st.markdown('<hr style="border:none;border-top:1px solid #1e2d3d;margin:0.7rem 0">',
                unsafe_allow_html=True)
    tombol_scrape = st.button("🔍  Mulai Scraping", type="primary")

# --- HEADER ---
st.markdown(f"""
<div class="page-header">
    <div class="badge">Prototipe v1.2 — Fix 403 + ScraperAPI</div>
    <h1>Scraper Data Tanah</h1>
    <p>Sumber: rumah123.com &nbsp;·&nbsp; Parser: __NEXT_DATA__ JSON &nbsp;·&nbsp;
       Target: {kota_pilihan}{" — " + kecamatan_input if kecamatan_input else ""}</p>
</div>
""", unsafe_allow_html=True)

# --- PANDUAN ---
with st.expander("ℹ️ Cara kerja & catatan penting", expanded=False):
    st.markdown("""
    **Strategi parsing**
    Rumah123 menggunakan Next.js dengan Server-Side Rendering. Data listing tersimpan di
    tag `<script id="__NEXT_DATA__">` dalam format JSON — lebih andal dari CSS selector
    yang bisa berubah kapan saja saat situs diupdate.

    **Langkah prototipe ini**
    1. Ambil HTML halaman 1 dengan `httpx`
    2. Ekstrak JSON dari `__NEXT_DATA__`
    3. Cari array listing di dalam struktur JSON secara rekursif
    4. Map field ke kolom Pangkalandata (Luas, Harga, Lokasi, Koordinat, Kontak)
    5. Cek duplikat vs file existing (jika diupload)
    6. Tampilkan hasil + tombol download Excel

    **Keterbatasan prototipe**
    - Hanya 1 halaman (±25 listing) — cukup untuk validasi field mapper
    - Belum ada pagination ke halaman 2, 3, dst
    - Jika `__NEXT_DATA__` tidak ditemukan, kemungkinan butuh Playwright (browser headless)

    **Kolom output kompatibel dengan Pangkalandata8.py**
    Hasil download bisa langsung diupload ke Pangkalandata untuk melihat peta & statistik.
    """)

# --- LOAD EXISTING DATA ---
df_existing = pd.DataFrame()
if file_existing:
    try:
        df_existing = pd.read_excel(file_existing)
        st.markdown(f'<div class="ok-box">✓ File existing dimuat: '
                    f'<b>{len(df_existing)}</b> baris sebagai referensi duplikat.</div>',
                    unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<div class="warn-box">⚠ Gagal membaca file existing: {e}</div>',
                    unsafe_allow_html=True)

# --- PROSES SCRAPING ---
if tombol_scrape:
    st.markdown("---")

    with st.spinner(f"Mengambil data dari rumah123.com — {kota_pilihan}..."):
        records, status_msg, debug_info = scrape_satu_halaman(
            kota_nama=kota_pilihan,
            kecamatan_filter=kecamatan_input,
            page=1,
            delay_min=jeda_min,
            delay_max=jeda_max,
            api_key=scraperapi_key,
        )

    # --- STATUS HASIL FETCH ---
    if not records:
        st.error(f"Scraping gagal: {status_msg}")

        st.markdown("**Debug info:**")
        st.json(debug_info)

        st.markdown("""
        <div class="warn-box">
        <b>Kemungkinan penyebab & solusi:</b><br><br>
        <b>Error 403 (paling umum dari Streamlit Cloud):</b><br>
        IP datacenter Streamlit Cloud dikenal sebagai bot oleh rumah123.
        Solusi: masukkan <b>ScraperAPI Key</b> di sidebar (daftar gratis di
        <a href="https://www.scraperapi.com" target="_blank">scraperapi.com</a> →
        1.000 request/bulan gratis, tidak butuh kartu kredit).<br><br>
        <b>Error lain:</b><br>
        • <b>__NEXT_DATA__ tidak ditemukan</b> → halaman CSR, perlu Playwright<br>
        • <b>401 ScraperAPI</b> → key salah atau kuota habis, cek di dashboard scraperapi.com<br>
        • <b>Struktur JSON berubah</b> → cek <code>sample_json</code> di debug info
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    df_hasil = pd.DataFrame(records)
    # Pastikan semua kolom output ada
    for kol in KOLOM_OUTPUT:
        if kol not in df_hasil.columns:
            df_hasil[kol] = ""
    df_hasil = df_hasil[KOLOM_OUTPUT]

    # --- CEK DUPLIKAT ---
    jumlah_duplikat = 0
    if not df_existing.empty:
        df_hasil, jumlah_duplikat = cek_dan_hapus_duplikat(df_hasil, df_existing)

    # --- METRIC CARDS ---
    total_raw    = len(records)
    total_bersih = len(df_hasil)
    valid_coords = df_hasil.dropna(subset=["Latitude", "Longitude"])
    valid_harga  = df_hasil[df_hasil["Harga_Total"] > 0]["Harga_Total"]
    rata2_harga  = valid_harga.mean() if not valid_harga.empty else 0

    def fmt_harga(v):
        if v >= 1e9:
            return f"Rp {v/1e9:.1f}M"
        elif v >= 1e6:
            return f"Rp {v/1e6:.0f}jt"
        return f"Rp {v:,.0f}"

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box g">
            <div class="lbl">Total Ditemukan</div>
            <div class="val">{total_raw}</div>
            <div class="sub">listing di halaman 1</div>
        </div>
        <div class="stat-box b">
            <div class="lbl">Data Baru</div>
            <div class="val">{total_bersih}</div>
            <div class="sub">{jumlah_duplikat} duplikat dibuang</div>
        </div>
        <div class="stat-box a">
            <div class="lbl">Ada Koordinat</div>
            <div class="val">{len(valid_coords)}</div>
            <div class="sub">siap diplot di peta</div>
        </div>
        <div class="stat-box r">
            <div class="lbl">Rata-rata Harga</div>
            <div class="val" style="font-size:1.1rem">{fmt_harga(rata2_harga)}</div>
            <div class="sub">per unit (bukan /m²)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- STATUS PARSING ---
    st.markdown(f'<div class="ok-box">✓ {status_msg} &nbsp;·&nbsp; '
                f'URL: <code>{debug_info.get("url","")}</code></div>',
                unsafe_allow_html=True)

    # --- TABEL HASIL ---
    st.markdown("#### Hasil Scraping")
    kolom_tampil = ["Nomor", "Judul_Iklan", "Kecamatan", "Kota",
                    "Luas_Tanah", "Harga_Total", "Harga_Tanah",
                    "Bukti_Kepemilikan", "Latitude", "Longitude",
                    "Kontak", "Agen"]
    kolom_ada = [c for c in kolom_tampil if c in df_hasil.columns]
    st.dataframe(
        df_hasil[kolom_ada],
        use_container_width=True,
        height=420,
        column_config={
            "Harga_Total":  st.column_config.NumberColumn("Harga Total (Rp)", format="%d"),
            "Harga_Tanah":  st.column_config.NumberColumn("Harga /m² (Rp)", format="%d"),
            "Luas_Tanah":   st.column_config.NumberColumn("Luas Tanah (m²)", format="%.1f"),
            "Latitude":     st.column_config.NumberColumn(format="%.6f"),
            "Longitude":    st.column_config.NumberColumn(format="%.6f"),
        }
    )

    # --- DOWNLOAD ---
    nama_file = (
        f"scraping_{kota_pilihan.lower().replace(' ','_')}"
        f"{'_' + kecamatan_input.replace(' ','_') if kecamatan_input else ''}"
        f"_{datetime.now():%Y%m%d_%H%M}.xlsx"
    )
    excel_bytes = to_excel_bytes(df_hasil)

    st.download_button(
        label="⬇  Download Excel",
        data=excel_bytes,
        file_name=nama_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

    st.caption(
        "File Excel ini kompatibel langsung dengan **Pangkalandata8.py** — "
        "upload file ini di Pangkalandata untuk melihat peta dan statistik harga."
    )

    # --- DEBUG EXPANDER ---
    with st.expander("🔧 Debug info (untuk developer)", expanded=False):
        st.json(debug_info)
        if not df_hasil.empty:
            st.markdown("**Sampel record pertama (raw):**")
            st.json(df_hasil.iloc[0].to_dict())
