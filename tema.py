"""Tema tampilan dashboard: palet PLN Mobile, mode gelap dan terang,
ikon garis, serta logo aplikasi.

Berkas ini hanya mengatur tampilan. Tidak ada angka yang dihitung di sini,
sehingga seluruh nilai pada dashboard tetap dibaca dari artefak notebook.

Ikon memakai gaya garis membulat seperti UIcons (flaticon.com/uicons) dan
ditanam langsung sebagai SVG, jadi tidak perlu sambungan internet dan tidak
ada emoji lagi. Bila ingin memakai berkas asli dari Flaticon, unduh ikonnya
dalam bentuk SVG lalu simpan ke folder "ikon" memakai nama kunci pada _JALUR
di bawah, misalnya ikon/rumah.svg. Berkas itu akan dipakai lebih dulu
daripada ikon bawaan.
"""

from __future__ import annotations

import base64
import html as _html
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote as _quote

import streamlit as st

DIR_TEMA = Path(__file__).resolve().parent
DIR_IKON = DIR_TEMA / "ikon"

# Palet PLN Mobile. Warna dasar diambil langsung dari logo aplikasi:
# biru tua, biru laut, teal, hijau limau, dan kuning pucat.
PALET = {
    "latar": "#03151f",
    "latar_kedua": "#072a3a",
    "kartu": "rgba(9, 42, 58, 0.72)",
    "kartu_terang": "rgba(14, 56, 76, 0.86)",
    "garis": "rgba(197, 232, 245, 0.12)",
    "utama": "#1592c0",
    "muda": "#4dbdc4",
    "tua": "#076c9e",
    "biru": "#3eaaae",
    "kuning": "#f3f1bf",
    "merah": "#e56458",
    "teks": "#eaf6fb",
    "redup": "#93b7c6",
}

# Palet dua mode tampilan. Warna aksen sama pada kedua mode karena diambil
# dari logo PLN Mobile; yang berbeda hanya latar, garis, dan warna tulisan.
AKSEN = "#1592c0"
AKSEN_TUA = "#076c9e"

PALET_GELAP = {
    "nama": "gelap",
    "latar1": "#0a4a66", "latar2": "#06222f", "latar3": "#03151f",
    "sisi_atas": "#062634", "sisi_bawah": "#03161f",
    "kartu": "rgba(9, 42, 58, 0.72)", "kartu_lembut": "rgba(9, 42, 58, 0.62)",
    "garis": "rgba(197, 232, 245, 0.12)",
    "garis_kuat": "rgba(197, 232, 245, 0.16)",
    "garis_tipis": "rgba(197, 232, 245, 0.10)",
    "isian": "rgba(255, 255, 255, 0.05)",
    "permukaan": "rgba(255, 255, 255, 0.03)",
    "bayang_kartu": "none",
    "bayang_logo": "rgba(2, 16, 24, 0.45)",
    "teks": "#eaf6fb", "judul": "#ffffff", "redup": "#93b7c6",
    "teks_sisi": "#cfe7f2", "label_sisi": "#7ba7bb",
    "nav_teks": "#c6e3f0", "nav_hover": "#ffffff",
    "lencana_teks": "#b7e6f5", "tab_aktif": "#ffffff",
    "aksen_teks": "#4dbdc4", "sapaan_akhir": "#072a3a",
    "utama": AKSEN, "muda": "#4dbdc4", "tua": AKSEN_TUA,
    "kisi": "rgba(197,232,245,0.10)", "sumbu": "rgba(197,232,245,0.16)",
    "hover_latar": "#072a3a",
    "cincin_latar": "rgba(255,255,255,0.05)",
    "cincin_rendah": "rgba(243,241,191,0.16)",
    "cincin_tinggi": "rgba(21,146,192,0.18)",
    "config": ("dark", "#03151f", "#072a3a", "#eaf6fb"),
}

PALET_TERANG = {
    "nama": "terang",
    "latar1": "#d8ecf7", "latar2": "#eef6fb", "latar3": "#f7fbfd",
    "sisi_atas": "#ffffff", "sisi_bawah": "#e8f3f9",
    "kartu": "rgba(255, 255, 255, 0.94)",
    "kartu_lembut": "rgba(255, 255, 255, 0.86)",
    "garis": "rgba(7, 108, 158, 0.16)",
    "garis_kuat": "rgba(7, 108, 158, 0.24)",
    "garis_tipis": "rgba(7, 108, 158, 0.12)",
    "isian": "rgba(255, 255, 255, 0.92)",
    "permukaan": "rgba(21, 146, 192, 0.08)",
    "bayang_kartu": "0 1px 2px rgba(7, 60, 90, 0.06), 0 8px 20px rgba(7, 60, 90, 0.08)",
    "bayang_logo": "rgba(7, 60, 90, 0.22)",
    "teks": "#143845", "judul": "#06293a", "redup": "#587c90",
    "teks_sisi": "#1d4a5c", "label_sisi": "#5f8ba0",
    "nav_teks": "#1d4a5c", "nav_hover": "#05506f",
    "lencana_teks": "#05628f", "tab_aktif": "#05506f",
    "aksen_teks": "#0d7ea8", "sapaan_akhir": "#3eaaae",
    "utama": AKSEN, "muda": "#0d7ea8", "tua": AKSEN_TUA,
    "kisi": "rgba(7, 60, 90, 0.12)", "sumbu": "rgba(7, 60, 90, 0.22)",
    "hover_latar": "#ffffff",
    "cincin_latar": "rgba(7, 60, 90, 0.06)",
    "cincin_rendah": "rgba(243, 209, 107, 0.24)",
    "cincin_tinggi": "rgba(21, 146, 192, 0.18)",
    "config": ("light", "#f7fbfd", "#e8f3f9", "#143845"),
}

MODE_BAWAAN = "gelap"


def mode_aktif() -> str:
    """Mode tampilan yang sedang dipakai: "gelap" atau "terang".

    Pilihan disimpan pada kunci "mode_tampilan" yang bukan kunci widget,
    sehingga tidak ikut terhapus ketika Streamlit menjalankan ulang skrip
    tanpa menggambar saklarnya. Inilah yang membuat mode terang bertahan.
    """
    try:
        pilihan = st.session_state.get("mode_tampilan")
    except Exception:
        return MODE_BAWAAN
    return pilihan if pilihan in ("gelap", "terang") else MODE_BAWAAN


def palet(mode: str | None = None) -> dict:
    """Kumpulan warna untuk mode yang sedang aktif."""
    return PALET_TERANG if (mode or mode_aktif()) == "terang" else PALET_GELAP


# Urutan warna untuk seluruh grafik Plotly, mengikuti gradasi logo.
URUTAN_WARNA = ["#1592c0", "#3eaaae", "#b1d591", "#f3f1bf", "#076c9e",
                "#6fd0e3", "#cbe36b", "#e56458"]

_SVG_BUNGKUS = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                'stroke-width="1.7" stroke-linecap="round" '
                'stroke-linejoin="round">%s</svg>')

# Kumpulan ikon garis membulat, satu kunci satu ikon.
_JALUR = {
    "rumah": ('<path d="M3.5 10.5 12 3.5l8.5 7"/>'
              '<path d="M5.6 9.9V20h12.8V9.9"/>'
              '<path d="M9.8 20v-5.6h4.4V20"/>'),
    "sapu": ('<path d="M14.5 3.5 20.5 9.5"/>'
             '<path d="M12.8 6.2 17.8 11.2 11.6 17.4a3 3 0 0 1-4.2 0L6.1 16.1'
             'a3 3 0 0 1 0-4.2z"/><path d="M4.2 19.8 6.6 17.4"/>'),
    "buku": ('<path d="M3.8 5.4h5.6a2 2 0 0 1 2 2v12.2a2.6 2.6 0 0 0-2.6-2H3.8z"/>'
             '<path d="M20.2 5.4h-5.6a2 2 0 0 0-2 2v12.2a2.6 2.6 0 0 1 2.6-2h5z"/>'),
    "pengguna": ('<circle cx="9" cy="8" r="3.2"/>'
                 '<path d="M3.2 20c0-3.3 2.6-5.4 5.8-5.4s5.8 2.1 5.8 5.4"/>'
                 '<path d="M16.4 5.6a3.2 3.2 0 0 1 0 6.2"/>'
                 '<path d="M17.6 14.9c1.9.8 3.2 2.5 3.2 5.1"/>'),
    "label": ('<path d="M20.4 12.6l-7.8 7.8a2 2 0 0 1-2.8 0L3.6 13.2V3.6h9.6'
              'l7.2 7.2a1.3 1.3 0 0 1 0 1.8z"/><circle cx="8" cy="8" r="1.5"/>'),
    "senyum": ('<circle cx="12" cy="12" r="8.4"/>'
               '<path d="M8.4 13.9c1 1.4 2.2 2.1 3.6 2.1s2.6-.7 3.6-2.1"/>'
               '<path d="M9.2 9.4h.02"/><path d="M14.8 9.4h.02"/>'),
    "robot": ('<rect x="4.6" y="7.2" width="14.8" height="12.2" rx="3"/>'
              '<path d="M12 4v3.2"/><path d="M9.4 12h.02"/><path d="M14.6 12h.02"/>'
              '<path d="M9.6 16.2h4.8"/>'),
    "folder": ('<path d="M3.6 7.4a2 2 0 0 1 2-2h3.3l2 2.4h7.5a2 2 0 0 1 2 2v8'
               'a2 2 0 0 1-2 2H5.6a2 2 0 0 1-2-2z"/>'),
    "basis_data": ('<ellipse cx="12" cy="6" rx="7.4" ry="2.9"/>'
                   '<path d="M4.6 6v12c0 1.6 3.3 2.9 7.4 2.9s7.4-1.3 7.4-2.9V6"/>'
                   '<path d="M4.6 12c0 1.6 3.3 2.9 7.4 2.9s7.4-1.3 7.4-2.9"/>'),
    "teks": '<path d="M4.8 5.6h14.4"/><path d="M4.8 12h9.6"/><path d="M4.8 18.4h12"/>',
    "grafik": ('<path d="M4 4v16h16"/><path d="M7.4 17v-5.4"/>'
               '<path d="M12 17V7.6"/><path d="M16.6 17v-3.4"/>'),
    "bintang": ('<path d="M12 3.8l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.8-5.2 2.8'
                'l1-5.8-4.2-4.1 5.8-.8z"/>'),
    "persen": ('<path d="M19 5 5 19"/><circle cx="7.5" cy="7.5" r="2.4"/>'
               '<circle cx="16.5" cy="16.5" r="2.4"/>'),
    "kilat": '<path d="M13.6 3 6 13.6h4.8L9.8 21 18 10.2h-5.2z"/>',
    "target": ('<circle cx="12" cy="12" r="8.4"/><circle cx="12" cy="12" r="4.4"/>'
               '<circle cx="12" cy="12" r="1"/>'),
    "dokumen": ('<path d="M13.4 3.6H7a2 2 0 0 0-2 2v12.8a2 2 0 0 0 2 2h10'
                'a2 2 0 0 0 2-2V9.2z"/><path d="M13.4 3.6V9.2H19"/>'
                '<path d="M8.4 13.4h7.2"/><path d="M8.4 16.8h4.6"/>'),
    "muat_ulang": '<path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20 4.4V10h-5.6"/>',
    "kaca": '<circle cx="10.6" cy="10.6" r="6.4"/><path d="M15.4 15.4 20.6 20.6"/>',
    "centang": '<path d="M4.6 12.6 9.4 17.4 19.4 6.6"/>',
    "silang": '<path d="M6.2 6.2 17.8 17.8"/><path d="M17.8 6.2 6.2 17.8"/>',
    "kotak": ('<rect x="4" y="4" width="16" height="16" rx="3"/>'
              '<path d="M8.4 12h7.2"/>'),
    "pengaturan": ('<path d="M4 7.6h9.4"/><path d="M18 7.6h2"/>'
                   '<circle cx="15.8" cy="7.6" r="2.2"/><path d="M4 16.4h2"/>'
                   '<path d="M10.4 16.4H20"/><circle cx="8.2" cy="16.4" r="2.2"/>'),
    "unduh": ('<path d="M12 3.8v10.6"/><path d="M7.6 10.4 12 14.8l4.4-4.4"/>'
              '<path d="M4.4 19.6h15.2"/>'),
    "mata": ('<path d="M2.6 12S6 5.8 12 5.8 21.4 12 21.4 12 18 18.2 12 18.2'
             ' 2.6 12 2.6 12z"/><circle cx="12" cy="12" r="3"/>'),
}

# Ikon untuk delapan halaman, berurutan sesuai menu navigasi.
IKON_NAVIGASI = ["rumah", "sapu", "buku", "pengguna", "label", "senyum",
                 "robot", "folder"]

# Pemetaan kata kunci label metrik ke nama ikon.
_IKON_KATA = [
    (("ulasan", "data", "baris", "dokumen", "korpus", "corpus"), "basis_data"),
    (("token", "kata", "teks", "kalimat"), "teks"),
    (("entitas", "label", "kelas", "subclass", "skema"), "label"),
    (("sentimen", "positif", "negatif", "netral"), "senyum"),
    (("f1", "skor", "akurasi", "presisi", "recall", "kinerja"), "target"),
    (("pakar", "kappa", "anotator", "validasi"), "pengguna"),
    (("persen", "rasio", "cakupan", "proporsi", "%"), "persen"),
    (("gambar", "grafik", "visual", "distribusi"), "grafik"),
    (("tabel", "berkas", "file", "folder", "arsip"), "folder"),
    (("model", "epoch", "pelatihan", "latih", "indobert"), "robot"),
    (("waktu", "durasi", "tahun", "periode"), "dokumen"),
]

# Logo PLN Mobile. Berkas PNG resmi dipakai lebih dulu, dan bila berkas itu
# tidak ada tersedia salinan vektor SVG dengan warna yang sama.
_BERKAS_LOGO = DIR_TEMA / "logo_pln_mobile.png"
_BERKAS_LOGO_SVG = DIR_TEMA / "logo_pln_mobile.svg"

LOGO_SVG = (
    '<svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg" '
    'role="img" aria-label="Logo PLN Mobile">'
    '<defs><linearGradient id="plnm" x1="0" y1="1" x2="1" y2="0">'
    '<stop offset="0" stop-color="#05628f"/>'
    '<stop offset="0.42" stop-color="#127da4"/>'
    '<stop offset="0.72" stop-color="#3eaaae"/>'
    '<stop offset="0.90" stop-color="#b1d591"/>'
    '<stop offset="1" stop-color="#f3f1bf"/>'
    '</linearGradient></defs>'
    '<rect width="240" height="240" rx="0" fill="url(#plnm)"/>'
    '<path d="M176 16 L118 100 H150 L134 168 L208 78 H166 Z" fill="#a9e7f7"/>'
    '<text x="26" y="126" font-size="58" font-weight="800" fill="#ffffff" '
    'font-family="Segoe UI, Helvetica, Arial, sans-serif" '
    'letter-spacing="1">PLN</text>'
    '<text x="26" y="192" font-size="62" font-weight="800" fill="#cbe36b" '
    'font-family="Segoe UI, Helvetica, Arial, sans-serif" '
    'letter-spacing="-1">mobile</text>'
    '</svg>'
)


@lru_cache(maxsize=1)
def logo_aplikasi() -> str:
    """Logo PLN Mobile siap tempel pada HTML.

    Berkas logo_pln_mobile.png ditanam sebagai data URI supaya logo resminya
    tampil apa adanya tanpa perlu sambungan internet. Bila berkas itu tidak
    ada, dipakai logo_pln_mobile.svg, lalu LOGO_SVG bawaan.
    """
    if _BERKAS_LOGO.is_file():
        try:
            data = base64.b64encode(_BERKAS_LOGO.read_bytes()).decode("ascii")
            return ('<img alt="Logo PLN Mobile" src="data:image/png;base64,%s"/>'
                    % data)
        except OSError:
            pass
    if _BERKAS_LOGO_SVG.is_file():
        try:
            return _BERKAS_LOGO_SVG.read_text(encoding="utf-8")
        except OSError:
            pass
    return LOGO_SVG


# Nama lama tetap disediakan agar pemanggilan sebelumnya tidak rusak.
LOGO_KOTAK = LOGO_SVG
LOGO_PLN = LOGO_SVG


def ikon(nama: str, kelas: str = "pln-ikon") -> str:
    """Mengembalikan satu ikon SVG siap tempel pada HTML.

    Bila ada berkas ikon/<nama>.svg, berkas itu yang dipakai sehingga ikon
    asli hasil unduhan dari Flaticon bisa langsung menggantikan ikon bawaan.
    """
    berkas = DIR_IKON / (nama + ".svg")
    if berkas.is_file():
        try:
            isi = berkas.read_text(encoding="utf-8")
        except OSError:
            isi = _SVG_BUNGKUS % _JALUR["kilat"]
    else:
        isi = _SVG_BUNGKUS % _JALUR.get(nama, _JALUR["kilat"])
    return "<span class='%s'>%s</span>" % (kelas, isi)


def ikon_untuk(label: str) -> str:
    """Memilih nama ikon berdasarkan kata pada label metrik."""
    kecil = (label or "").lower()
    for kata, nama in _IKON_KATA:
        for k in kata:
            if k in kecil:
                return nama
    return "kilat"


def _uri_ikon(nama: str) -> str:
    """Ikon dalam bentuk data URI, dipakai sebagai mask CSS pada menu."""
    berkas = DIR_IKON / (nama + ".svg")
    if berkas.is_file():
        try:
            isi = berkas.read_text(encoding="utf-8")
        except OSError:
            isi = _SVG_BUNGKUS % _JALUR["kilat"]
    else:
        isi = _SVG_BUNGKUS % _JALUR.get(nama, _JALUR["kilat"])
    isi = isi.replace('stroke="currentColor"', 'stroke="#000000"')
    if "xmlns" not in isi:
        isi = isi.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    return "data:image/svg+xml," + _quote(isi, safe="")

_CSS_DASAR = """
<style>
.stApp {
  background: radial-gradient(1200px 620px at 10% -12%, var(--pln-latar1) 0%,
              var(--pln-latar2) 46%, var(--pln-latar3) 100%);
  color: var(--pln-teks);
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container {
  padding-top: 1.7rem; padding-bottom: 3.2rem;
  padding-left: 2.2rem; padding-right: 2.2rem; max-width: 1560px;
}

h1, h2, h3, h4 { color: var(--pln-judul); font-weight: 700; letter-spacing: -0.01em; }
h1 { font-size: 1.62rem; margin: 0 0 0.35rem; }
h2 { font-size: 1.24rem; margin: 0.15rem 0 0.45rem; }
h3 { font-size: 1.06rem; margin: 0.15rem 0 0.4rem; }

/* Perapian jarak: satu irama untuk tulisan, tabel, dan gambar. */
[data-testid="stVerticalBlock"] { gap: 1.1rem; }
[data-testid="stHorizontalBlock"] {
  gap: 1.4rem; align-items: stretch; row-gap: 1.4rem;
}
[data-testid="stMarkdownContainer"] p { margin-bottom: 0.45rem; line-height: 1.6; }
[data-testid="stMarkdownContainer"] ul, [data-testid="stMarkdownContainer"] ol {
  margin-top: 0.15rem; margin-bottom: 0.35rem;
}
[data-testid="stCaptionContainer"] p { margin-bottom: 0.15rem; color: var(--pln-redup); }
hr {
  margin: 1.6rem 0 !important;
  border-color: var(--pln-garis) !important;
}
[data-testid="stImage"] { margin: 0; }
[data-testid="stImage"] img {
  border-radius: 14px; border: 1px solid var(--pln-garis);
  background: #ffffff;
}
[data-testid="stImage"] figcaption, [data-testid="stImageCaption"] {
  color: var(--pln-redup); font-size: 0.82rem; padding-top: 6px;
}
[data-testid="stDataFrame"] {
  border-radius: 14px; overflow: hidden;
  border: 1px solid var(--pln-garis);
}
[data-testid="stDataFrame"] * { font-size: 0.86rem; }
.stButton, .stDownloadButton { margin-top: 0.3rem; }
.stPlotlyChart { margin: 0; }

/* Sisi kiri */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, var(--pln-sisi-atas) 0%, var(--pln-sisi-bawah) 100%);
  border-right: 1px solid var(--pln-garis-tipis);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.1rem; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.7rem; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: var(--pln-teks-sisi); }

/* Tombol */
.stButton > button, .stDownloadButton > button {
  background: linear-gradient(135deg, #1592c0 0%, #076c9e 100%);
  color: #ffffff; border: none; border-radius: 12px;
  padding: 0.5rem 1.05rem; font-weight: 600;
  box-shadow: 0 8px 20px rgba(21, 146, 192, 0.26);
}
.stButton > button:hover, .stDownloadButton > button:hover {
  filter: brightness(1.08); color: #ffffff;
}
.stButton > button:focus, .stDownloadButton > button:focus { color: #ffffff; }

/* Kotak masukan */
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea, [data-baseweb="select"] > div {
  background: var(--pln-isian) !important;
  border: 1px solid var(--pln-garis-kuat) !important;
  border-radius: 11px !important; color: var(--pln-teks) !important;
}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
  padding: 0.62rem 0.85rem !important; font-size: 0.9rem !important;
  line-height: 1.5 !important;
}
[data-testid="stTextArea"] textarea {
  padding: 0.7rem 0.9rem !important; font-size: 0.9rem !important;
  line-height: 1.65 !important;
}
[data-baseweb="select"] > div {
  min-height: 42px !important; padding: 0 0.35rem !important;
  font-size: 0.9rem !important;
}
[data-baseweb="select"] input { font-size: 0.9rem !important; }
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
  color: var(--pln-redup) !important; opacity: 1 !important;
}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {
  border-color: rgba(21, 146, 192, 0.65) !important;
}

/* Label widget: ukuran dan jarak seragam terhadap kotaknya. */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
  font-size: 0.86rem !important; font-weight: 600; color: var(--pln-teks);
  line-height: 1.45; margin: 0 0 0.35rem !important;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  color: var(--pln-teks-sisi);
}
[data-testid="stCheckbox"] p, [data-testid="stToggle"] p,
[data-testid="stRadio"] p { font-size: 0.88rem; }

/* Irama judul dan tulisan biasa pada badan halaman. */
[data-testid="stMarkdownContainer"] h2 { margin: 0.35rem 0 0.55rem; }
[data-testid="stMarkdownContainer"] h3 {
  font-size: 1.14rem; margin: 0.3rem 0 0.5rem;
}
[data-testid="stMarkdownContainer"] h4 {
  font-size: 1rem; margin: 0.25rem 0 0.4rem;
}
[data-testid="stMarkdownContainer"] code {
  background: var(--pln-permukaan); border: 1px solid var(--pln-garis-tipis);
  border-radius: 7px; padding: 0.08rem 0.34rem; font-size: 0.85em;
  color: var(--pln-aksen-teks);
}
[data-testid="stCode"] pre, pre[class*="language-"] {
  background: var(--pln-permukaan) !important;
  border: 1px solid var(--pln-garis) !important;
  border-radius: 12px !important; padding: 0.9rem 1rem !important;
}

/* Metrik bawaan, pemberitahuan, tab, dan pelipat */
[data-testid="stMetric"] {
  background: var(--pln-kartu);
  border: 1px solid var(--pln-garis);
  border-radius: 16px; padding: 18px 20px;
}
[data-testid="stMetricLabel"] p {
  color: var(--pln-redup); font-size: 0.78rem; font-weight: 600;
  letter-spacing: 0.03em; line-height: 1.4;
}
[data-testid="stMetricValue"] {
  color: var(--pln-judul); font-weight: 700; font-size: 1.5rem;
  line-height: 1.25;
}
[data-testid="stMetricDelta"] { font-size: 0.8rem; }
[data-testid="stAlert"] {
  border-radius: 14px; border: 1px solid var(--pln-garis-kuat);
  background: var(--pln-kartu-lembut); color: var(--pln-teks);
  padding: 0.95rem 1.1rem;
}
[data-testid="stAlert"] p { margin-bottom: 0.2rem; line-height: 1.6; }
[data-testid="stExpander"] details {
  background: var(--pln-kartu-lembut);
  border: 1px solid var(--pln-garis);
  border-radius: 14px;
}
[data-testid="stExpander"] summary {
  color: var(--pln-teks); font-weight: 600; font-size: 0.92rem;
  padding: 0.72rem 1rem;
}
[data-testid="stExpander"] details > div { padding: 0.2rem 1rem 0.9rem; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: none; }
.stTabs [data-baseweb="tab"] {
  background: var(--pln-permukaan); border-radius: 11px 11px 0 0;
  padding: 8px 16px; color: var(--pln-redup);
}
.stTabs [aria-selected="true"] {
  background: rgba(21, 146, 192, 0.22); color: var(--pln-tab-aktif);
}

::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(21, 146, 192, 0.40); border-radius: 8px;
}
</style>
"""

_CSS_KOMPONEN = """
<style>
/* Ikon garis */
.pln-ikon svg, .pln-ikon-kotak svg { width: 100%; height: 100%; display: block; }
.pln-ikon { width: 18px; height: 18px; display: inline-block; color: inherit; }
.pln-ikon-kotak {
  width: 46px; height: 46px; flex: 0 0 46px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #1592c0 0%, #076c9e 100%);
  color: #ffffff; box-shadow: 0 8px 18px rgba(21, 146, 192, 0.28);
}
.pln-ikon-kotak svg { width: 22px; height: 22px; }

/* Merek dan logo pada bilah sisi */
.pln-merek {
  display: flex; align-items: center; gap: 13px; padding: 4px 2px 16px;
}
.pln-merek .logo {
  width: 48px; height: 48px; flex: 0 0 48px; border-radius: 13px;
  overflow: hidden; box-shadow: 0 8px 18px var(--pln-bayang-logo);
}
.pln-merek .logo svg, .pln-merek .logo img {
  width: 100%; height: 100%; display: block; object-fit: cover;
}
.pln-merek .nama {
  font-weight: 700; font-size: 0.98rem; color: var(--pln-judul); line-height: 1.15;
}
.pln-merek .catatan {
  font-size: 0.74rem; color: var(--pln-redup); letter-spacing: 0.02em; margin-top: 2px;
}
.pln-label-sisi {
  font-size: 0.7rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--pln-label-sisi); margin: 18px 0 10px; font-weight: 700;
}

/* Menu navigasi: satu tombol panjang per halaman, berjarak lega. */
[data-testid="stSidebar"] div[role="radiogroup"] {
  display: flex; flex-direction: column; gap: 12px;
  margin: 4px 0 12px; padding: 0;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label {
  display: flex; align-items: center; justify-content: flex-start;
  text-align: left; gap: 14px;
  width: 100%; box-sizing: border-box; min-height: 52px;
  padding: 12px 16px; margin: 0;
  border-radius: 13px; border: 1px solid var(--pln-garis-tipis);
  background: var(--pln-permukaan); color: var(--pln-nav-teks); cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label::before {
  content: ""; flex: 0 0 21px; width: 21px; height: 21px;
  background-color: currentColor;
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center;
  -webkit-mask-size: 21px 21px; mask-size: 21px 21px;
}
/* Hanya ikon dan tulisan menu yang tampil. Lingkaran radio bawaan Streamlit
   disembunyikan pada kedalaman mana pun: yang dibiarkan hidup hanya kotak
   tulisan, pembungkusnya, dan isi kotak tulisan itu sendiri. */
[data-testid="stSidebar"] div[role="radiogroup"] > label input { display: none !important; }
[data-testid="stSidebar"] div[role="radiogroup"] > label
  *:not([data-testid="stMarkdownContainer"]):not(:has([data-testid="stMarkdownContainer"])):not([data-testid="stMarkdownContainer"] *) {
  display: none !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label *:has([data-testid="stMarkdownContainer"])::before,
[data-testid="stSidebar"] div[role="radiogroup"] > label *:has([data-testid="stMarkdownContainer"])::after {
  content: none !important; display: none !important;
}
/* Tulisan selalu rata kiri dan sejajar untuk seluruh menu. */
[data-testid="stSidebar"] div[role="radiogroup"] > label *:has([data-testid="stMarkdownContainer"]) {
  flex: 1 1 auto; min-width: 0; margin: 0; padding: 0;
  display: flex; align-items: center; justify-content: flex-start;
  text-align: left;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label [data-testid="stMarkdownContainer"] {
  width: 100%; text-align: left;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label p {
  margin: 0; font-size: 0.94rem; font-weight: 600; line-height: 1.3;
  color: inherit; text-align: left; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
  background: rgba(21, 146, 192, 0.16); border-color: rgba(21, 146, 192, 0.34);
  color: var(--pln-nav-hover);
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: linear-gradient(135deg, #1592c0 0%, #076c9e 100%);
  color: #ffffff; border-color: transparent;
  box-shadow: 0 10px 22px rgba(21, 146, 192, 0.30);
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:focus-within {
  outline: 2px solid rgba(21, 146, 192, 0.55); outline-offset: 2px;
}

/* Saklar mode gelap dan terang */
[data-testid="stSidebar"] [data-testid="stToggle"] { margin: 0 0 4px; }
[data-testid="stSidebar"] [data-testid="stToggle"] label { gap: 12px; align-items: center; }
[data-testid="stSidebar"] [data-testid="stToggle"] p {
  font-size: 0.9rem; font-weight: 600; color: var(--pln-teks-sisi);
}

/* Kartu: hanya wadah yang diberi penanda oleh tema.kartu() */
div.pln-tanda-kartu { display: none; }
div[data-testid="stElementContainer"]:has(> div > div.pln-tanda-kartu),
div[data-testid="element-container"]:has(> div > div.pln-tanda-kartu) {
  display: none !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div > div > div > div.pln-tanda-kartu),
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div > div > div > div > div.pln-tanda-kartu) {
  background: var(--pln-kartu);
  border: 1px solid var(--pln-garis);
  border-radius: 18px; padding: 20px 22px 18px;
  height: 100%;
}

/* Kepala halaman */
.pln-kepala {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 18px; padding: 2px 0 20px; flex-wrap: wrap;
}
.pln-kepala .jejak {
  font-size: 0.76rem; color: var(--pln-redup); letter-spacing: 0.04em;
  margin: 0 0 3px; font-weight: 600;
}
.pln-kepala .judul {
  font-size: 1.5rem; font-weight: 700; color: var(--pln-judul); margin: 0;
  line-height: 1.2;
}
.pln-lencana {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(21, 146, 192, 0.16); border: 1px solid rgba(21, 146, 192, 0.34);
  color: var(--pln-lencana-teks); border-radius: 999px; padding: 6px 14px;
  font-size: 0.78rem; font-weight: 600;
}

/* Kartu metrik: satu grid rapi, jarak antar kartu selalu sama. */
.pln-baris {
  display: flex; flex-wrap: wrap; align-items: stretch;
  gap: 18px; margin: 2px 0 18px;
}
.pln-baris > .pln-metrik { flex: 1 1 228px; min-width: 228px; }
.pln-metrik {
  box-sizing: border-box; height: 100%; min-height: 146px;
  background: var(--pln-kartu);
  border: 1px solid var(--pln-garis-kuat);
  border-radius: 18px; padding: 20px 22px 18px;
  box-shadow: var(--pln-bayang-kartu);
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px;
}
.pln-metrik .kiri {
  min-width: 0; flex: 1 1 auto; display: flex; flex-direction: column;
}
.pln-metrik .label {
  font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--pln-redup); font-weight: 700; line-height: 1.35;
  margin: 0 0 10px; min-height: 2.5em;
}
.pln-metrik .nilai {
  font-size: 1.56rem; font-weight: 700; color: var(--pln-judul);
  margin: 0 0 10px; line-height: 1.2; letter-spacing: -0.015em;
  word-break: break-word;
}
.pln-metrik .beda {
  font-size: 0.78rem; color: var(--pln-redup); margin: auto 0 0;
  line-height: 1.5;
}
.pln-metrik .beda b { color: var(--pln-aksen-teks); font-weight: 700; }
@media (max-width: 640px) {
  .pln-baris { gap: 14px; }
  .pln-baris > .pln-metrik { flex: 1 1 100%; min-width: 0; }
  .pln-metrik { min-height: 0; padding: 18px; }
  .pln-metrik .label { min-height: 0; }
}

/* Kartu sapaan dan judul bagian */
.pln-sapaan {
  background: linear-gradient(135deg, #076c9e 0%, #1592c0 55%, var(--pln-sapaan-akhir) 100%);
  border: 1px solid var(--pln-garis-kuat);
  border-radius: 20px; padding: 24px 26px; min-height: 100%;
  box-sizing: border-box;
  display: flex; flex-direction: column; justify-content: center; gap: 2px;
}
.pln-sapaan .halo {
  font-size: 0.79rem; color: #d6f0fa; margin: 0 0 5px; letter-spacing: 0.03em;
}
.pln-sapaan .sapa {
  font-size: 1.3rem; font-weight: 700; color: #ffffff; margin: 0 0 13px;
  line-height: 1.2;
}
.pln-sapaan .judul {
  font-size: 1.05rem; font-weight: 700; color: #ffffff; margin: 0 0 7px;
  line-height: 1.32;
}
.pln-sapaan .tanda {
  font-size: 0.88rem; color: #eaf8ff; margin: 0 0 13px; line-height: 1.6;
  max-width: 56ch;
}
.pln-sapaan .tanda:last-child { margin-bottom: 0; }
.pln-sapaan .jejak {
  align-self: flex-start; margin: 0; padding: 5px 13px;
  font-size: 0.78rem; font-weight: 600; color: #ffffff; line-height: 1.4;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.26); border-radius: 999px;
}
.pln-judul-bagian {
  font-size: 0.99rem; font-weight: 700; color: var(--pln-judul);
  margin: 0 0 7px; display: flex; align-items: center; gap: 8px;
}
.pln-ket-bagian {
  font-size: 0.81rem; color: var(--pln-redup); margin: 0 0 13px; line-height: 1.55;
}

/* Bayangan kartu wadah, terasa pada mode terang. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div > div > div > div.pln-tanda-kartu),
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div > div > div > div > div.pln-tanda-kartu) {
  box-shadow: var(--pln-bayang-kartu);
}
</style>
"""

def _css_navigasi() -> str:
    """Menyusun aturan CSS ikon menu, satu ikon untuk setiap halaman."""
    aturan = ["<style>"]
    for nomor, nama in enumerate(IKON_NAVIGASI, start=1):
        uri = _uri_ikon(nama)
        aturan.append(
            '[data-testid="stSidebar"] div[role="radiogroup"] > '
            "label:nth-of-type(%d)::before {"
            ' -webkit-mask-image: url("%s"); mask-image: url("%s"); }'
            % (nomor, uri, uri)
        )
    aturan.append("</style>")
    return "\n".join(aturan)


def _css_variabel(mode: str) -> str:
    """Menyusun variabel warna, dipakai bersama oleh mode gelap dan terang."""
    p = palet(mode)
    pasangan = [
        ("--pln-latar1", p["latar1"]), ("--pln-latar2", p["latar2"]),
        ("--pln-latar3", p["latar3"]),
        ("--pln-sisi-atas", p["sisi_atas"]), ("--pln-sisi-bawah", p["sisi_bawah"]),
        ("--pln-kartu", p["kartu"]), ("--pln-kartu-lembut", p["kartu_lembut"]),
        ("--pln-garis", p["garis"]), ("--pln-garis-kuat", p["garis_kuat"]),
        ("--pln-garis-tipis", p["garis_tipis"]),
        ("--pln-isian", p["isian"]), ("--pln-permukaan", p["permukaan"]),
        ("--pln-bayang-kartu", p["bayang_kartu"]),
        ("--pln-bayang-logo", p["bayang_logo"]),
        ("--pln-teks", p["teks"]), ("--pln-judul", p["judul"]),
        ("--pln-redup", p["redup"]), ("--pln-teks-sisi", p["teks_sisi"]),
        ("--pln-label-sisi", p["label_sisi"]),
        ("--pln-nav-teks", p["nav_teks"]), ("--pln-nav-hover", p["nav_hover"]),
        ("--pln-lencana-teks", p["lencana_teks"]),
        ("--pln-tab-aktif", p["tab_aktif"]),
        ("--pln-aksen-teks", p["aksen_teks"]),
        ("--pln-sapaan-akhir", p["sapaan_akhir"]),
    ]
    aturan = " ".join("%s: %s;" % butir for butir in pasangan)
    return "<style>:root { %s }</style>" % aturan


def _selaraskan_tema_bawaan(mode: str) -> None:
    """Menyamakan tema bawaan Streamlit (tabel, menu, kalender) dengan mode."""
    try:
        from streamlit import config as _config

        dasar, latar, latar_kedua, warna_teks = palet(mode)["config"]
        _config.set_option("theme.base", dasar)
        _config.set_option("theme.backgroundColor", latar)
        _config.set_option("theme.secondaryBackgroundColor", latar_kedua)
        _config.set_option("theme.textColor", warna_teks)
        _config.set_option("theme.primaryColor", AKSEN)
    except Exception:
        # Bila versi Streamlit tidak mengizinkannya, tampilan tetap benar
        # karena seluruh permukaan utama sudah diatur lewat CSS di bawah.
        pass


def terapkan(mode: str | None = None) -> None:
    """Memasang seluruh gaya tampilan. Cukup dipanggil sekali di app.py."""
    mode = mode or mode_aktif()
    st.session_state["mode_tampilan"] = mode
    _selaraskan_tema_bawaan(mode)
    sebelumnya = st.session_state.get("_mode_terpasang")
    st.session_state["_mode_terpasang"] = mode

    st.markdown(_css_variabel(mode), unsafe_allow_html=True)
    st.markdown(_CSS_DASAR, unsafe_allow_html=True)
    st.markdown(_CSS_KOMPONEN, unsafe_allow_html=True)
    st.markdown(_css_navigasi(), unsafe_allow_html=True)

    # Sekali jalan ulang ketika mode berganti, supaya tema bawaan Streamlit
    # (tabel dan menu) ikut terkirim ke peramban dengan warna yang baru.
    if sebelumnya is not None and sebelumnya != mode:
        try:
            st.rerun()
        except Exception:
            pass


def _ganti_mode() -> None:
    """Menyimpan pilihan saklar ke kunci menetap saat saklar digeser."""
    terang = bool(st.session_state.get("_saklar_terang"))
    st.session_state["mode_tampilan"] = "terang" if terang else "gelap"


def saklar_mode() -> str:
    """Saklar mode gelap dan terang pada bilah sisi.

    Nilai saklar selalu dibaca ulang dari kunci menetap, sehingga tampilan
    terang bertahan sampai pengguna sendiri yang mematikannya.
    """
    mode = mode_aktif()
    st.sidebar.markdown("<p class='pln-label-sisi'>Tampilan</p>",
                        unsafe_allow_html=True)
    st.sidebar.toggle(
        "Mode terang",
        value=(mode == "terang"),
        key="_saklar_terang",
        on_change=_ganti_mode,
        help="Pilihan tampilan bertahan selama aplikasi dibuka.",
    )
    return mode


def _aman(teks) -> str:
    """Mengamankan teks agar aman ditaruh di dalam HTML."""
    return _html.escape(str(teks), quote=True)


def tanda_kartu() -> None:
    """Menandai wadah saat ini agar digambar sebagai kartu kaca."""
    st.markdown("<div class='pln-tanda-kartu'></div>", unsafe_allow_html=True)


def kartu(batas: bool = True):
    """Wadah bergaya kartu. Dipakai dengan pernyataan with.

    Contoh:
        with tema.kartu():
            st.dataframe(bingkai)
    """
    wadah = st.container(border=batas)
    with wadah:
        tanda_kartu()
    return wadah


def merek_bilah_sisi(nama: str = "PLN Mobile Analytics",
                     catatan: str = "Corpus domain IndoBERT") -> None:
    """Blok logo PLN dan nama dashboard di puncak bilah sisi."""
    st.sidebar.markdown(
        "<div class='pln-merek'><div class='logo'>%s</div><div>"
        "<div class='nama'>%s</div><div class='catatan'>%s</div></div></div>"
        % (logo_aplikasi(), _aman(nama), _aman(catatan)),
        unsafe_allow_html=True,
    )


def label_sisi(teks: str) -> None:
    """Label kecil pemisah bagian pada bilah sisi."""
    st.sidebar.markdown("<p class='pln-label-sisi'>%s</p>" % _aman(teks),
                        unsafe_allow_html=True)


def kepala_halaman(jejak: str, judul: str, lencana: str = "") -> None:
    """Kepala halaman: jejak navigasi, judul, dan lencana metodologi."""
    kanan = ""
    if lencana:
        kanan = ("<div class='pln-lencana'>%s%s</div>"
                 % (ikon("kilat"), _aman(lencana)))
    st.markdown(
        "<div class='pln-kepala'><div><p class='jejak'>%s</p>"
        "<p class='judul'>%s</p></div>%s</div>"
        % (_aman(jejak), _aman(judul), kanan),
        unsafe_allow_html=True,
    )


def judul_bagian(judul: str, keterangan: str = "") -> None:
    """Judul dan keterangan seragam di atas tabel maupun gambar."""
    nama_ikon = ikon_untuk(judul)
    bagian = ["<p class='pln-judul-bagian'>%s%s</p>"
              % (ikon(nama_ikon), _aman(judul))]
    if keterangan:
        bagian.append("<p class='pln-ket-bagian'>%s</p>" % _aman(keterangan))
    st.markdown("".join(bagian), unsafe_allow_html=True)


def kartu_metrik(daftar) -> None:
    """Baris kartu metrik bergaya kaca dengan ikon garis.

    Setiap butir boleh berbentuk (label, nilai), (label, nilai, bantuan),
    atau (label, nilai, bantuan, nama_ikon).
    """
    kotak = []
    for butir in daftar:
        if not butir:
            continue
        label = butir[0] if len(butir) > 0 else ""
        nilai = butir[1] if len(butir) > 1 else ""
        bantuan = butir[2] if len(butir) > 2 else ""
        nama_ikon = butir[3] if len(butir) > 3 else ikon_untuk(str(label))
        beda = ("<p class='beda'>%s</p>" % _aman(bantuan)) if bantuan else ""
        kotak.append(
            "<div class='pln-metrik'><div class='kiri'>"
            "<p class='label'>%s</p><p class='nilai'>%s</p>%s</div>"
            "<div class='pln-ikon-kotak'>%s</div></div>"
            % (_aman(label), _aman(nilai), beda,
               ikon(nama_ikon, kelas="pln-ikon-dalam"))
        )
    if not kotak:
        return
    st.markdown("<div class='pln-baris'>%s</div>" % "".join(kotak),
                unsafe_allow_html=True)


def kartu_sapaan(nama: str, kalimat: str, tanda: str = "",
                 judul: str = "") -> None:
    """Kartu sambutan bergradasi biru PLN Mobile di halaman Ringkasan.

    Urutan isinya: sapaan singkat, nama pemilik dashboard, judul tebal,
    kalimat penjelas, lalu satu lencana kecil berisi keterangan tambahan.
    """
    bagian = ["<div class='pln-sapaan'>",
              "<p class='halo'>Selamat datang kembali</p>",
              "<p class='sapa'>%s</p>" % _aman(nama)]
    if judul:
        bagian.append("<p class='judul'>%s</p>" % _aman(judul))
    if kalimat:
        bagian.append("<p class='tanda'>%s</p>" % _aman(kalimat))
    if tanda:
        bagian.append("<p class='jejak'>%s</p>" % _aman(tanda))
    bagian.append("</div>")
    st.markdown("".join(bagian), unsafe_allow_html=True)

def gaya_plotly(gambar, tinggi: int | None = None):
    """Menyeragamkan grafik Plotly dengan mode tampilan yang sedang aktif."""
    p = palet()
    try:
        gambar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=p["teks_sisi"], size=12,
                      family="Segoe UI, Helvetica, Arial, sans-serif"),
            colorway=URUTAN_WARNA,
            title_font=dict(color=p["judul"], size=15),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=p["redup"])),
            hoverlabel=dict(bgcolor=p["hover_latar"], bordercolor=p["utama"],
                            font=dict(color=p["teks"])),
            margin=dict(l=8, r=8, t=42, b=8),
        )
        gambar.update_xaxes(gridcolor=p["kisi"], griddash="dot",
                            zeroline=False, linecolor=p["sumbu"],
                            tickfont=dict(color=p["redup"]))
        gambar.update_yaxes(gridcolor=p["kisi"], griddash="dot",
                            zeroline=False, linecolor=p["sumbu"],
                            tickfont=dict(color=p["redup"]))
        if isinstance(tinggi, int) and not isinstance(tinggi, bool) and tinggi > 0:
            gambar.update_layout(height=tinggi)
    except Exception:
        # Grafik tetap ditampilkan meskipun penyeragaman gaya gagal.
        pass
    return gambar


def kartu_cincin(nilai: float | None, judul: str, keterangan: str = "",
                 maksimum: float = 1.0, tinggi: int = 240) -> bool:
    """Cincin skor. Angkanya berasal dari tabel hasil, bukan hitungan baru."""
    if nilai is None:
        return False
    p = palet()
    try:
        import plotly.graph_objects as go

        gambar = go.Figure(go.Indicator(
            mode="gauge+number",
            value=float(nilai),
            number=dict(font=dict(color=p["judul"], size=34),
                        valueformat=".3f"),
            title=dict(text=judul, font=dict(color=p["redup"], size=13)),
            gauge=dict(
                axis=dict(range=[0, maksimum], tickcolor=p["redup"],
                          tickfont=dict(color=p["label_sisi"], size=9)),
                bar=dict(color=p["utama"], thickness=0.3),
                bgcolor=p["cincin_latar"],
                borderwidth=0,
                steps=[
                    dict(range=[0, maksimum * 0.6],
                         color=p["cincin_rendah"]),
                    dict(range=[maksimum * 0.6, maksimum],
                         color=p["cincin_tinggi"]),
                ],
            ),
        ))
        gambar.update_layout(height=tinggi, margin=dict(l=12, r=12, t=34, b=6),
                             paper_bgcolor="rgba(0,0,0,0)",
                             plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(gambar, use_container_width=True)
        if keterangan:
            st.markdown("<p class='pln-ket-bagian'>%s</p>" % _aman(keterangan),
                        unsafe_allow_html=True)
        return True
    except Exception:
        st.metric(judul, "%.3f" % float(nilai))
        if keterangan:
            st.caption(keterangan)
        return True
