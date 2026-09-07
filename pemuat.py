"""Lapisan pemuatan artefak dashboard.

Berkas ini sengaja dibuat tanpa ketergantungan pada Streamlit supaya logika
pembacaan zip hasil notebook dapat diuji secara mandiri, sedangkan app.py
hanya berperan sebagai lapisan tampilan.

Struktur zip yang dihasilkan sel "DASHBOARD 1" pada notebook:

    dashboard_corpus_pln/
        data/           seluruh tabel hasil (.csv/.xlsx)
        gambar/         seluruh gambar hasil (.png)
        model/          model_ner_subclass, model_ner_entity, model_sentimen_terbaik
        manifest.json   daftar berkas beserta judul tabelnya
        ringkasan.json  angka utama untuk kartu metrik

Bila manifest tidak ditemukan, kelas Zip tetap dapat bekerja dengan cara
memindai seluruh berkas .csv/.xlsx/.png di bawah folder akar. Dengan begitu
folder mentah Google Drive (output_preparation, output_ner_bio, dan seterusnya)
juga dapat dibaca langsung tanpa proses ekspor.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

NAMA_FOLDER_ZIP = "dashboard_corpus_pln"
EKSTENSI_TABEL = (".csv", ".xlsx", ".parquet")
EKSTENSI_GAMBAR = (".png", ".jpg", ".jpeg", ".webp")

# Folder yang tidak perlu dipindai karena berisi bobot model atau checkpoint.
FOLDER_DIABAIKAN = ("model", "__pycache__", ".git", ".streamlit")


# ----------------------------------------------------------------------------
# Penentuan folder akar zip
# ----------------------------------------------------------------------------
def kandidat_akar(tambahan: Optional[str] = None) -> List[Path]:
    """Menyusun daftar lokasi yang mungkin memuat zip hasil notebook."""
    daftar: List[Path] = []

    def tambah(nilai) -> None:
        if not nilai:
            return
        jalur = Path(str(nilai)).expanduser()
        if jalur not in daftar:
            daftar.append(jalur)

    tambah(tambahan)
    tambah(os.environ.get("PLN_DASHBOARD_DATA"))

    di_sini = Path(__file__).resolve().parent
    for basis in (Path.cwd(), di_sini, di_sini.parent):
        tambah(basis / NAMA_FOLDER_ZIP)
        tambah(basis)

    # Jalur khas Google Colab dan Google Drive Desktop.
    tambah(Path("/content/drive/MyDrive/Programming") / NAMA_FOLDER_ZIP)
    tambah(Path("/content/drive/MyDrive/Programming"))
    tambah(Path.home() / "Google Drive" / "My Drive" / "Programming" / NAMA_FOLDER_ZIP)
    return daftar


def _terlihat_seperti_zip(jalur: Path) -> bool:
    """Menilai apakah sebuah folder berisi artefak yang dibutuhkan dashboard."""
    if not jalur.is_dir():
        return False
    if (jalur / "manifest.json").exists():
        return True
    if (jalur / "data").is_dir() or (jalur / "gambar").is_dir():
        return True
    # Folder mentah hasil notebook.
    for nama in ("output_preparation", "output_sentimen", "output_modeling",
                 "output_ner_bio", "output_visualisasi"):
        if (jalur / nama).is_dir():
            return True
    return False


def resolve_akar(tambahan: Optional[str] = None) -> Optional[Path]:
    """Mengembalikan folder akar zip pertama yang valid, atau None."""
    for kandidat in kandidat_akar(tambahan):
        try:
            if _terlihat_seperti_zip(kandidat):
                return kandidat.resolve()
        except OSError:
            continue
    return None


# ----------------------------------------------------------------------------
# Kelas utama
# ----------------------------------------------------------------------------
class Zip:
    """Pembungkus satu folder hasil ekspor notebook."""

    def __init__(self, akar) -> None:
        self.akar = Path(akar).resolve()
        self._indeks_tabel: Optional[Dict[str, Path]] = None
        self._indeks_gambar: Optional[Dict[str, Path]] = None
        self._manifest: Optional[List[dict]] = None
        self._ringkasan: Optional[dict] = None

    # -- properti folder ---------------------------------------------------
    @property
    def dir_data(self) -> Path:
        jalur = self.akar / "data"
        return jalur if jalur.is_dir() else self.akar

    @property
    def dir_gambar(self) -> Path:
        jalur = self.akar / "gambar"
        return jalur if jalur.is_dir() else self.akar

    @property
    def dir_model(self) -> Path:
        return self.akar / "model"

    def ada(self) -> bool:
        return self.akar.is_dir()

    # -- berkas metadata ---------------------------------------------------
    @property
    def manifest(self) -> List[dict]:
        if self._manifest is None:
            berkas = self.akar / "manifest.json"
            data: List[dict] = []
            if berkas.exists():
                try:
                    isi = json.loads(berkas.read_text(encoding="utf-8"))
                    if isinstance(isi, list):
                        data = [b for b in isi if isinstance(b, dict)]
                except (json.JSONDecodeError, OSError):
                    data = []
            self._manifest = data
        return self._manifest

    @property
    def ringkasan(self) -> dict:
        if self._ringkasan is None:
            berkas = self.akar / "ringkasan.json"
            data: dict = {}
            if berkas.exists():
                try:
                    isi = json.loads(berkas.read_text(encoding="utf-8"))
                    if isinstance(isi, dict):
                        data = isi
                except (json.JSONDecodeError, OSError):
                    data = {}
            self._ringkasan = data
        return self._ringkasan

    def judul(self, nama: str) -> str:
        """Judul manusiawi sebuah berkas, diambil dari manifest bila tersedia."""
        dasar = Path(nama).name
        for baris in self.manifest:
            if str(baris.get("nama", "")).lower() == dasar.lower():
                judul = str(baris.get("judul") or "").strip()
                if judul:
                    return judul
        return Path(dasar).stem.replace("_", " ").capitalize()

    # -- pengindeksan berkas ----------------------------------------------
    def _pindai(self, ekstensi) -> Dict[str, Path]:
        indeks: Dict[str, Path] = {}
        if not self.akar.is_dir():
            return indeks
        for berkas in sorted(self.akar.rglob("*")):
            if not berkas.is_file() or berkas.suffix.lower() not in ekstensi:
                continue
            bagian = berkas.relative_to(self.akar).parts[:-1]
            if any(b in FOLDER_DIABAIKAN or b.startswith("checkpoint-") for b in bagian):
                continue
            kunci = berkas.name.lower()
            # Berkas pada folder data/gambar diprioritaskan atas duplikat lain.
            if kunci in indeks and indeks[kunci].parent.name in ("data", "gambar"):
                continue
            indeks[kunci] = berkas
        return indeks

    @property
    def indeks_tabel(self) -> Dict[str, Path]:
        if self._indeks_tabel is None:
            self._indeks_tabel = self._pindai(EKSTENSI_TABEL)
        return self._indeks_tabel

    @property
    def indeks_gambar(self) -> Dict[str, Path]:
        if self._indeks_gambar is None:
            self._indeks_gambar = self._pindai(EKSTENSI_GAMBAR)
        return self._indeks_gambar

    # -- pencarian ---------------------------------------------------------
    def cari_tabel(self, *nama: str) -> Optional[Path]:
        """Mencari berkas tabel berdasarkan nama tepat, lalu pola wildcard."""
        indeks = self.indeks_tabel
        for kandidat in nama:
            kunci = Path(str(kandidat)).name.lower()
            if kunci in indeks:
                return indeks[kunci]
            if not kunci.endswith(EKSTENSI_TABEL):
                for ekstensi in EKSTENSI_TABEL:
                    if kunci + ekstensi in indeks:
                        return indeks[kunci + ekstensi]
        for kandidat in nama:
            pola = Path(str(kandidat)).name.lower()
            if not any(t in pola for t in "*?["):
                pola = "*%s*" % pola.rsplit(".", 1)[0]
            cocok = sorted(k for k in indeks if fnmatch.fnmatch(k, pola))
            if cocok:
                return indeks[cocok[0]]
        return None

    def cari_gambar(self, *nama: str) -> Optional[Path]:
        """Mencari satu berkas gambar berdasarkan nama atau pola."""
        hasil = self.daftar_gambar(*nama)
        return hasil[0] if hasil else None

    def daftar_gambar(self, *pola: str) -> List[Path]:
        """Mengembalikan seluruh gambar yang cocok dengan pola yang diberikan."""
        indeks = self.indeks_gambar
        if not pola:
            return [indeks[k] for k in sorted(indeks)]
        hasil: List[Path] = []
        for kandidat in pola:
            kunci = Path(str(kandidat)).name.lower()
            if kunci in indeks and indeks[kunci] not in hasil:
                hasil.append(indeks[kunci])
                continue
            uji = kunci if any(t in kunci for t in "*?[") else "*%s*" % kunci.rsplit(".", 1)[0]
            for k in sorted(indeks):
                if fnmatch.fnmatch(k, uji) and indeks[k] not in hasil:
                    hasil.append(indeks[k])
        return hasil

    def daftar_tabel(self, *pola: str) -> List[Path]:
        """Mengembalikan seluruh tabel yang cocok dengan pola yang diberikan."""
        indeks = self.indeks_tabel
        if not pola:
            return [indeks[k] for k in sorted(indeks)]
        hasil: List[Path] = []
        for kandidat in pola:
            kunci = Path(str(kandidat)).name.lower()
            uji = kunci if any(t in kunci for t in "*?[") else "*%s*" % kunci.rsplit(".", 1)[0]
            for k in sorted(indeks):
                if fnmatch.fnmatch(k, uji) and indeks[k] not in hasil:
                    hasil.append(indeks[k])
        return hasil

    # -- pembacaan ---------------------------------------------------------
    def baca(self, *nama: str, indeks_kolom_pertama: bool = False) -> Optional[pd.DataFrame]:
        """Membaca tabel pertama yang cocok menjadi DataFrame."""
        berkas = self.cari_tabel(*nama)
        if berkas is None:
            return None
        return baca_tabel(berkas, indeks_kolom_pertama=indeks_kolom_pertama)

    # -- model -------------------------------------------------------------
    def model(self, nama: str) -> Optional[Path]:
        """Mengembalikan folder model bila berisi berkas konfigurasi."""
        for kandidat in (self.dir_model / nama, self.akar / "output_modeling" / nama,
                         self.akar / nama):
            if (kandidat / "config.json").exists():
                return kandidat
        return None

    def daftar_model(self) -> Dict[str, Optional[Path]]:
        return {
            "model_ner_subclass": self.model("model_ner_subclass"),
            "model_ner_entity": self.model("model_ner_entity"),
            "model_sentimen_terbaik": self.model("model_sentimen_terbaik"),
        }


# ----------------------------------------------------------------------------
# Pembacaan tabel
# ----------------------------------------------------------------------------
def baca_tabel(berkas, indeks_kolom_pertama: bool = False) -> Optional[pd.DataFrame]:
    """Membaca satu berkas .csv, .xlsx, atau .parquet dengan penanganan galat."""
    berkas = Path(berkas)
    if not berkas.exists():
        return None
    akhiran = berkas.suffix.lower()
    try:
        if akhiran == ".parquet":
            bingkai = pd.read_parquet(berkas)
        elif akhiran == ".xlsx":
            bingkai = pd.read_excel(berkas)
        else:
            bingkai = pd.read_csv(berkas)
    except Exception:
        try:
            bingkai = pd.read_csv(berkas, sep=None, engine="python",
                                  encoding="utf-8", on_bad_lines="skip")
        except Exception:
            return None
    if indeks_kolom_pertama and len(bingkai.columns):
        kolom_pertama = bingkai.columns[0]
        if str(kolom_pertama).startswith("Unnamed") or bingkai[kolom_pertama].dtype == object:
            bingkai = bingkai.set_index(kolom_pertama)
            bingkai.index.name = None if str(kolom_pertama).startswith("Unnamed") else kolom_pertama
    return bingkai


def kolom_pertama_cocok(bingkai: pd.DataFrame, *kandidat: str) -> Optional[str]:
    """Mencari nama kolom pertama yang cocok, tidak peka huruf besar kecil."""
    if bingkai is None or not len(bingkai.columns):
        return None
    peta = {str(k).strip().lower(): str(k) for k in bingkai.columns}
    for nama in kandidat:
        kunci = str(nama).strip().lower()
        if kunci in peta:
            return peta[kunci]
    for nama in kandidat:
        kunci = str(nama).strip().lower()
        for k_kecil, k_asli in peta.items():
            if kunci in k_kecil:
                return k_asli
    return None


def angka_saja(bingkai: pd.DataFrame) -> List[str]:
    """Daftar kolom bertipe angka pada sebuah DataFrame."""
    if bingkai is None:
        return []
    return [str(k) for k in bingkai.columns
            if pd.api.types.is_numeric_dtype(bingkai[k])]


# ----------------------------------------------------------------------------
# Praproses teks untuk halaman prediksi langsung
# ----------------------------------------------------------------------------
POLA_URL = re.compile(r"https?://\S+|www\.\S+")
POLA_MENTION = re.compile(r"[@#]\w+")
POLA_BUKAN_HURUF = re.compile(r"[^a-z\s]")
POLA_ULANG = re.compile(r"(.)\1{2,}")
POLA_SPASI = re.compile(r"\s+")


def muat_kamus_slang(berkas) -> Dict[str, str]:
    """Memuat kamus kata tidak baku dari berkas dua kolom."""
    bingkai = baca_tabel(berkas)
    if bingkai is None or bingkai.shape[1] < 2:
        return {}
    asal, tujuan = bingkai.columns[0], bingkai.columns[1]
    kamus: Dict[str, str] = {}
    for a, b in zip(bingkai[asal], bingkai[tujuan]):
        if pd.isna(a) or pd.isna(b):
            continue
        kamus[str(a).strip().lower()] = str(b).strip().lower()
    return kamus


def bersihkan_teks(teks: str, kamus_slang: Optional[Dict[str, str]] = None) -> str:
    """Praproses ringkas yang meniru rantai praproses BAGIAN 3 notebook.

    Tahapan: penurunan huruf, pembuangan URL dan mention, pembuangan angka dan
    tanda baca, penormalan huruf berulang, penggantian kata tidak baku, lalu
    perapian spasi. Stemming tidak diterapkan agar bentuk kata tetap dikenali
    tokenizer IndoBERT saat inferensi.
    """
    isi = str(teks or "").lower()
    isi = POLA_URL.sub(" ", isi)
    isi = POLA_MENTION.sub(" ", isi)
    isi = POLA_BUKAN_HURUF.sub(" ", isi)
    isi = POLA_ULANG.sub(r"\1\1", isi)
    token = [t for t in POLA_SPASI.sub(" ", isi).strip().split(" ") if t]
    if kamus_slang:
        token = [kamus_slang.get(t, t) for t in token]
        token = [t for t in " ".join(token).split(" ") if t]
    return " ".join(token)


# ----------------------------------------------------------------------------
# Pembantu tampilan
# ----------------------------------------------------------------------------
def format_angka(nilai, satuan: str = "", desimal: Optional[int] = None) -> str:
    """Memformat angka menjadi teks kartu metrik yang mudah dibaca."""
    if nilai is None or (isinstance(nilai, float) and pd.isna(nilai)):
        return "-"
    try:
        angka = float(nilai)
    except (TypeError, ValueError):
        return str(nilai)
    if desimal is None:
        desimal = 0 if float(angka).is_integer() else 4
    if desimal == 0:
        teks = format(int(round(angka)), ",").replace(",", ".")
    else:
        teks = ("%." + str(desimal) + "f") % angka
        teks = teks.replace(".", ",")
    return (teks + " " + satuan).strip()


def ambil(kamus: dict, *jalur, bawaan=None):
    """Mengambil nilai bersarang dari kamus dengan aman."""
    kini = kamus
    for kunci in jalur:
        if not isinstance(kini, dict) or kunci not in kini:
            return bawaan
        kini = kini[kunci]
    return kini if kini is not None else bawaan
