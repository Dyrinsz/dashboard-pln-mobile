"""Pemeriksaan cepat sebelum menjalankan dashboard.

Jalankan dari dalam folder dashboard_pln:

    python cek_lingkungan.py

Skrip ini tidak menjalankan Streamlit. Fungsinya memastikan versi Python,
pustaka, berkas aplikasi, dan folder artefak sudah siap, sehingga penyebab galat
ketahuan sebelum perintah streamlit run dijalankan.
"""

import importlib
import os
import sys
from pathlib import Path

AKAR_SKRIP = Path(__file__).resolve().parent
BERKAS_APLIKASI = ["app.py", "pemuat.py", "inferensi.py", "requirements.txt"]
PUSTAKA_WAJIB = ["streamlit", "pandas", "numpy", "plotly", "pyarrow",
                 "openpyxl", "PIL"]
PUSTAKA_OPSIONAL = ["torch", "transformers"]

masalah = []
catatan = []


def tanda(ok):
    return "OK" if ok else "HILANG"


print("=" * 66)
print("PEMERIKSAAN LINGKUNGAN DASHBOARD PLN MOBILE")
print("=" * 66)

versi = sys.version_info
print("Python      :", "%d.%d.%d" % (versi.major, versi.minor, versi.micro))
print("Penerjemah  :", sys.executable)
if versi < (3, 9):
    masalah.append("Python terlalu lama. Gunakan versi 3.10 sampai 3.12.")
elif versi >= (3, 13):
    catatan.append("Python 3.13 masih sering gagal memasang torch. Halaman lain tetap aman.")

di_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
print("Lingkungan  :", "virtual (.venv aktif)" if di_venv else "Python sistem")
if not di_venv:
    catatan.append("Lingkungan virtual belum aktif. Di VS Code, pilih penerjemah berlabel .venv.")

print("-" * 66)
print("BERKAS APLIKASI")
for nama in BERKAS_APLIKASI:
    ok = (AKAR_SKRIP / nama).is_file()
    print("   {:<18} {}".format(nama, tanda(ok)))
    if not ok:
        masalah.append("Berkas " + nama + " tidak ada di " + str(AKAR_SKRIP))

print("-" * 66)
print("PUSTAKA WAJIB")
for nama in PUSTAKA_WAJIB:
    try:
        modul = importlib.import_module(nama)
        versi_modul = getattr(modul, "__version__", "terpasang")
        print("   {:<18} OK      {}".format(nama, versi_modul))
    except Exception:
        print("   {:<18} BELUM ADA".format(nama))
        masalah.append("Pustaka " + nama + " belum terpasang.")

print("-" * 66)
print("PUSTAKA OPSIONAL (halaman Prediksi Langsung)")
for nama in PUSTAKA_OPSIONAL:
    try:
        modul = importlib.import_module(nama)
        print("   {:<18} OK      {}".format(nama, getattr(modul, "__version__", "terpasang")))
    except Exception:
        print("   {:<18} belum ada, halaman lain tetap berfungsi".format(nama))

print("-" * 66)
print("FOLDER ARTEFAK")
sys.path.insert(0, str(AKAR_SKRIP))
try:
    import pemuat

    lingkungan = os.environ.get("PLN_DASHBOARD_DATA")
    if lingkungan:
        print("   PLN_DASHBOARD_DATA :", lingkungan)
    akar = pemuat.resolve_akar()
    if akar is None:
        print("   Zip dashboard_corpus_pln belum ditemukan.")
        print("   Lokasi yang dicoba:")
        for kandidat in pemuat.kandidat_akar():
            print("      -", kandidat)
        masalah.append("Folder dashboard_corpus_pln belum ditemukan.")
    else:
        zip_artefak = pemuat.Zip(akar)
        jumlah_tabel = len(zip_artefak.indeks_tabel)
        jumlah_gambar = len(zip_artefak.indeks_gambar)
        jumlah_model = len(zip_artefak.daftar_model())
        print("   Ditemukan  :", akar)
        print("   Tabel      :", jumlah_tabel)
        print("   Gambar     :", jumlah_gambar)
        print("   Model      :", jumlah_model)
        print("   manifest   :", tanda(bool(zip_artefak.manifest)))
        print("   ringkasan  :", tanda(bool(zip_artefak.ringkasan)))
        if jumlah_tabel == 0:
            masalah.append("Zip ditemukan tetapi tidak berisi tabel apa pun.")
        if jumlah_model == 0:
            catatan.append("Folder model kosong. Halaman Prediksi Langsung tidak aktif.")
except Exception as galat:
    print("   Gagal memeriksa zip:", galat)
    masalah.append("pemuat.py gagal dijalankan: " + str(galat))

print("=" * 66)
if masalah:
    print("PERLU DIPERBAIKI:")
    for i, teks in enumerate(dict.fromkeys(masalah), 1):
        print("  {}. {}".format(i, teks))
else:
    print("SEMUA SIAP. Jalankan: streamlit run app.py")
if catatan:
    print("-" * 66)
    print("CATATAN:")
    for i, teks in enumerate(dict.fromkeys(catatan), 1):
        print("  {}. {}".format(i, teks))
print("=" * 66)
