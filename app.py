"""Dashboard Streamlit - Analisis Pengaduan Pengguna PLN Mobile.

Aplikasi ini hanya menyajikan kembali artefak yang sudah dihasilkan notebook
Thesis_Program_V28.ipynb. Tidak ada pelatihan model dan tidak ada perhitungan
ulang metrik di sini, sehingga angka pada dashboard selalu identik dengan angka
pada notebook dan pada naskah penelitian.

Jalankan dengan:
    streamlit run app.py
"""

from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

import inferensi
import pemuat
import tema
from pemuat import Zip, ambil, format_angka, kolom_pertama_cocok

# ---------------------------------------------------------------------------
# Konfigurasi halaman
# ---------------------------------------------------------------------------
# Ikon tab peramban memakai logo PLN Mobile bila berkasnya ada.
_BERKAS_IKON = Path(__file__).resolve().parent / "logo_pln_mobile.png"

st.set_page_config(
    page_title="Dashboard Pengaduan PLN Mobile",
    page_icon=(str(_BERKAS_IKON) if _BERKAS_IKON.is_file()
               else ":material/bolt:"),
    layout="wide",
    initial_sidebar_state="expanded",
)


def _pindahkan_rahasia() -> None:
    """Menyalin Secrets Streamlit Cloud menjadi variabel lingkungan.

    Berguna saat dashboard tayang daring: token Hugging Face untuk repo model
    privat dan lokasi artefak dapat diatur lewat menu Settings > Secrets tanpa
    mengubah kode. Di komputer sendiri fungsi ini tidak melakukan apa-apa.
    """
    for kunci in ("HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN", "PLN_DASHBOARD_DATA"):
        try:
            nilai = st.secrets.get(kunci)
        except Exception:
            return
        if nilai and not os.environ.get(kunci):
            os.environ[kunci] = str(nilai)


_pindahkan_rahasia()

# Tampilan (gelap atau terang) disuntikkan sekali di sini, sebelum
# komponen apa pun dibuat. Mode mengikuti saklar pada bilah sisi.
tema.terapkan()

JUDUL_APLIKASI = "Dashboard Pengaduan Pengguna PLN Mobile"
SUBJUDUL = (
    "Analisis dan Perancangan Dashboard Pengaduan Pengguna PLN Mobile "
    "Berbasis Corpus Domain-Spesifik Menggunakan Model IndoBERT"
)
PENULIS_SINGKAT = "Heidyr Hadiningrat"
LENCANA = "IndoBERT · CRISP-DM · Corpus domain PLN"

# Wadah navigasi bilah sisi, diisi bilah_sisi() agar menu tampil di puncak.
_WADAH_NAV = None

# Warna sentimen memakai turunan palet logo PLN Mobile.
WARNA_SENTIMEN = {"NEGATIF": "#e56458", "NETRAL": "#f3d06b",
                  "POSITIF": "#8cc96b", "TIDAK YAKIN": "#7ba7bb"}


# ---------------------------------------------------------------------------
# Pemuatan berkas dengan cache
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def dapatkan_zip(akar: str) -> Zip:
    return Zip(akar)


@st.cache_data(show_spinner=False)
def baca_tabel_cache(jalur: str, indeks_kolom_pertama: bool = False):
    return pemuat.baca_tabel(jalur, indeks_kolom_pertama=indeks_kolom_pertama)


def tabel(zip_artefak: Zip, *nama: str, indeks_kolom_pertama: bool = False):
    """Mencari lalu membaca satu tabel, mengembalikan None bila tidak ada."""
    berkas = zip_artefak.cari_tabel(*nama)
    if berkas is None:
        return None
    return baca_tabel_cache(str(berkas), indeks_kolom_pertama)


# ---------------------------------------------------------------------------
# Komponen tampilan yang dipakai berulang
# ---------------------------------------------------------------------------
def pesan_kosong(nama_berkas: str, catatan: str = "") -> None:
    """Pemberitahuan seragam ketika sebuah artefak belum tersedia."""
    teks = "Berkas **%s** belum tersedia pada folder data." % nama_berkas
    if catatan:
        teks += " " + catatan
    st.info(teks)


def tampilkan_tabel(zip_artefak: Zip, *nama: str, judul: str | None = None,
                    keterangan: str = "", indeks_kolom_pertama: bool = False,
                    tinggi: int | None = None,
                    unduh: bool = True) -> pd.DataFrame | None:
    """Menampilkan satu tabel lengkap dengan judul, keterangan, dan unduhan."""
    berkas = zip_artefak.cari_tabel(*nama)
    if berkas is None:
        pesan_kosong(nama[0])
        return None

    bingkai = baca_tabel_cache(str(berkas), indeks_kolom_pertama)
    if bingkai is None or bingkai.empty:
        pesan_kosong(berkas.name, "Berkas ditemukan tetapi isinya kosong.")
        return None

    # Sebagian versi Streamlit menolak height=None, jadi argumen tinggi
    # hanya dikirim bila memang berisi bilangan positif.
    argumen_tabel = {"use_container_width": True}
    if isinstance(tinggi, int) and not isinstance(tinggi, bool) and tinggi > 0:
        argumen_tabel["height"] = tinggi

    with tema.kartu():
        tema.judul_bagian(judul or zip_artefak.judul(berkas.name), keterangan)
        st.dataframe(bingkai, **argumen_tabel)
        if unduh:
            st.download_button(
                "Unduh %s" % berkas.name,
                data=bingkai.to_csv(index=indeks_kolom_pertama).encode("utf-8"),
                file_name=berkas.name,
                mime="text/csv",
                key="unduh_" + berkas.name,
            )
    return bingkai


def tampilkan_gambar(zip_artefak: Zip, *nama: str, judul: str = "",
                     lebar: int | None = None) -> bool:
    """Menampilkan satu gambar hasil notebook bila tersedia."""
    berkas = zip_artefak.cari_gambar(*nama)
    if berkas is None:
        pesan_kosong(nama[0])
        return False

    keterangan_gambar = judul or zip_artefak.judul(berkas.name)
    with tema.kartu():
        tema.judul_bagian(keterangan_gambar)
        if isinstance(lebar, int) and not isinstance(lebar, bool) and lebar > 0:
            st.image(str(berkas), width=lebar)
        else:
            st.image(str(berkas), use_container_width=True)
    return True


def grafik_batang(bingkai: pd.DataFrame, kolom_label: str, kolom_nilai: str,
                  judul: str = "", mendatar: bool = False, warna=None,
                  urutkan: bool = True, batas: int | None = None) -> None:
    """Grafik batang seragam memakai Plotly dengan cadangan bawaan Streamlit."""
    if bingkai is None or bingkai.empty:
        return
    data = bingkai[[kolom_label, kolom_nilai]].dropna().copy()
    data[kolom_nilai] = pd.to_numeric(data[kolom_nilai], errors="coerce")
    data = data.dropna()
    if urutkan:
        data = data.sort_values(kolom_nilai, ascending=False)
    if batas:
        data = data.head(batas)
    if data.empty:
        return

    try:
        import plotly.express as px

        if mendatar:
            data = data.sort_values(kolom_nilai)
            gambar = px.bar(data, x=kolom_nilai, y=kolom_label, orientation="h",
                            title=judul, text=kolom_nilai,
                            color=kolom_label if warna else None,
                            color_discrete_map=warna or {})
        else:
            gambar = px.bar(data, x=kolom_label, y=kolom_nilai, title=judul,
                            text=kolom_nilai,
                            color=kolom_label if warna else None,
                            color_discrete_map=warna or {})
        gambar.update_traces(texttemplate="%{text:,.4~f}", textposition="outside",
                             cliponaxis=False)
        if not warna:
            gambar.update_traces(marker_color=tema.URUTAN_WARNA[0],
                                 marker_line_width=0)
        gambar.update_layout(showlegend=False, height=420,
                             margin=dict(l=10, r=10, t=60 if judul else 20, b=10),
                             xaxis_title=None, yaxis_title=None)
        tema.gaya_plotly(gambar)
        st.plotly_chart(gambar, use_container_width=True)
    except Exception:
        if judul:
            st.markdown("**%s**" % judul)
        st.bar_chart(data.set_index(kolom_label)[kolom_nilai])


def kartu_metrik(daftar) -> None:
    """Menampilkan sederet kartu metrik dalam satu baris."""
    tema.kartu_metrik(daftar)


# ---------------------------------------------------------------------------
# Bilah sisi
# ---------------------------------------------------------------------------
def bilah_sisi() -> Zip | None:
    global _WADAH_NAV
    tema.merek_bilah_sisi("PLN Mobile Analytics", "Corpus domain IndoBERT")
    _WADAH_NAV = st.sidebar.container()
    tema.saklar_mode()
    st.sidebar.markdown("<p class='pln-label-sisi'>Pengaturan data</p>",
                        unsafe_allow_html=True)

    otomatis = pemuat.resolve_akar()
    bawaan = str(otomatis) if otomatis else ""
    jalur = st.sidebar.text_input(
        "Folder artefak (dashboard_corpus_pln)",
        value=st.session_state.get("jalur_data", bawaan),
        help=("Folder hasil sel DASHBOARD 1 pada notebook. Boleh juga diisi "
              "folder Programming yang memuat output_preparation dan kawan-kawan."),
    )
    st.session_state["jalur_data"] = jalur

    if not jalur:
        return None

    akar = pemuat.resolve_akar(jalur)
    if akar is None:
        st.sidebar.error("Folder tidak ditemukan atau tidak berisi artefak notebook.")
        return None

    zip_artefak = dapatkan_zip(str(akar))
    st.sidebar.success("Artefak terbaca")
    st.sidebar.caption("Lokasi: %s" % akar)
    st.sidebar.caption("%d tabel · %d gambar"
                       % (len(zip_artefak.indeks_tabel), len(zip_artefak.indeks_gambar)))

    if st.sidebar.button("Muat ulang data", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

    with st.sidebar.expander("Status model terlatih"):
        for nama, folder in zip_artefak.daftar_model().items():
            if folder is None:
                st.write("Belum ada: %s" % nama)
            else:
                st.write("Tersedia: %s (%.0f MB)" % (nama, inferensi.ukuran_folder_mb(folder)))

    st.sidebar.divider()
    st.sidebar.caption(SUBJUDUL)
    return zip_artefak


# ---------------------------------------------------------------------------
# Halaman 1 - Ringkasan
# ---------------------------------------------------------------------------
def skor_unggulan(zip_artefak: Zip):
    """Mengambil satu skor terbaik dari artefak untuk cincin di kartu atas.

    Nilainya dibaca dari tabel hasil evaluasi, bukan dihitung ulang, sehingga
    tetap sama dengan angka pada notebook dan naskah penelitian.
    """
    banding = tabel(zip_artefak, "tabel_perbandingan_skema_ner.csv")
    if banding is not None and not banding.empty:
        kolom = kolom_pertama_cocok(banding, "F1 Score", "f1")
        if kolom:
            nilai = pd.to_numeric(banding[kolom], errors="coerce").dropna()
            if len(nilai):
                puncak = float(nilai.max())
                if puncak > 1.0:
                    puncak = puncak / 100.0
                return puncak, "F1 terbaik model NER"

    fold = tabel(zip_artefak, "tabel_hasil_per_fold.csv")
    if fold is not None and not fold.empty:
        kolom = kolom_pertama_cocok(fold, "F1 Macro")
        if kolom:
            nilai = pd.to_numeric(fold[kolom], errors="coerce").dropna()
            nilai = nilai[nilai <= 1.0001]
            if len(nilai):
                return float(nilai.mean()), "Rata-rata Macro-F1 sentimen"
    return None, ""


def halaman_ringkasan(zip_artefak: Zip) -> None:
    kolom_sapaan, kolom_cincin = st.columns([3, 2])
    with kolom_sapaan:
        tema.kartu_sapaan(
            PENULIS_SINGKAT,
            "Dashboard ini digunakan untuk mengeksplorasi karakteristik, "
            "kategori, sentimen, dan performa model dalam menganalisis "
            "ulasan pengguna PLN Mobile.",
            "%d tabel dan %d gambar terbaca dari zip"
            % (len(zip_artefak.indeks_tabel), len(zip_artefak.indeks_gambar)),
            judul="Visualisasi Hasil Analisis Pengaduan Pengguna",
        )
    with kolom_cincin:
        nilai_skor, judul_skor = skor_unggulan(zip_artefak)
        tema.kartu_cincin(nilai_skor, judul_skor or "Skor model",
                          "Dibaca dari tabel hasil evaluasi pada zip.")

    st.subheader("Ringkasan Hasil Penelitian")
    ringkasan = zip_artefak.ringkasan

    kartu_metrik([
        ("Jumlah ulasan", format_angka(ambil(ringkasan, "corpus", "jumlah_dokumen")),
         "Banyak dokumen pada corpus akhir"),
        ("Total token", format_angka(ambil(ringkasan, "corpus", "total_token")),
         "Jumlah seluruh token corpus"),
        ("Kosakata unik", format_angka(ambil(ringkasan, "corpus", "kosakata_unik")),
         "Ukuran vocabulary corpus"),
        ("Type Token Ratio", format_angka(ambil(ringkasan, "corpus", "type_token_ratio"), desimal=5),
         "Rasio keberagaman kata"),
        ("OOV tipe kata", format_angka(ambil(ringkasan, "corpus", "oov_tipe_persen"), "%", 2),
         "Kata yang tidak ada pada Indo4B"),
        ("OOV token", format_angka(ambil(ringkasan, "corpus", "oov_token_persen"), "%", 2),
         "Bagian token corpus di luar Indo4B"),
        ("Cakupan kamus domain", format_angka(ambil(ringkasan, "corpus", "cakupan_kamus_persen"), "%", 2),
         "Dictionary coverage istilah kelistrikan"),
        ("Cakupan dokumen", format_angka(ambil(ringkasan, "corpus", "cakupan_dokumen_persen"), "%", 2),
         "Document coverage istilah kelistrikan"),
    ])

    st.divider()
    kolom_kiri, kolom_kanan = st.columns([3, 2])

    with kolom_kiri:
        rekap = tampilkan_tabel(
            zip_artefak, "rekapitulasi_hasil_analisis.csv",
            judul="Rekapitulasi Angka Utama",
            keterangan="Seluruh indikator utama yang dilaporkan pada naskah penelitian.",
            tinggi=430,
        )
        if rekap is None:
            tampilkan_tabel(zip_artefak, "tabel_evaluasi_akhir_kinerja_model.csv",
                            judul="Evaluasi Akhir Kinerja Model")

    with kolom_kanan:
        banding = tabel(zip_artefak, "tabel_perbandingan_skema_ner.csv")
        if banding is not None:
            kolom_skema = kolom_pertama_cocok(banding, "Skema")
            kolom_f1 = kolom_pertama_cocok(banding, "F1 Score", "f1")
            if kolom_skema and kolom_f1:
                grafik_batang(banding, kolom_skema, kolom_f1,
                              judul="F1 Score Dua Skema Pelabelan NER")

        fold = tabel(zip_artefak, "tabel_hasil_per_fold.csv")
        if fold is not None:
            kolom_macro = kolom_pertama_cocok(fold, "F1 Macro")
            if kolom_macro:
                nilai = pd.to_numeric(fold[kolom_macro], errors="coerce").dropna()
                nilai = nilai[nilai <= 1.0001]
                if len(nilai):
                    st.metric("Macro-F1 sentimen (rata-rata lipatan)",
                              format_angka(nilai.mean(), desimal=4),
                              "± %s" % format_angka(nilai.std(ddof=1) if len(nilai) > 1 else 0,
                                                    desimal=4),
                              delta_color="off")

    st.divider()
    st.markdown("**Spesifikasi lingkungan dan model**")
    kolom_a, kolom_b = st.columns(2)
    lingkungan = ambil(ringkasan, "lingkungan", bawaan={}) or {}
    model = ambil(ringkasan, "model", bawaan={}) or {}
    with kolom_a:
        if lingkungan:
            st.dataframe(pd.DataFrame(sorted(lingkungan.items()),
                                      columns=["Pustaka", "Versi"]),
                         use_container_width=True, hide_index=True)
        else:
            pesan_kosong("ringkasan.json", "Jalankan sel DASHBOARD 1 pada notebook.")
    with kolom_b:
        parameter = model.get("parameter") or {}
        baris = [("Model pralatih", model.get("pralatih", "-")),
                 ("Perangkat pelatihan", model.get("perangkat_pelatihan", "-"))]
        baris += list(parameter.items())
        if baris:
            st.dataframe(pd.DataFrame(baris, columns=["Parameter", "Nilai"]),
                         use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Halaman 2 - Data dan praproses
# ---------------------------------------------------------------------------
def halaman_praproses(zip_artefak: Zip) -> None:
    st.subheader("Data dan Tahapan Praproses")

    kolom_kiri, kolom_kanan = st.columns(2)
    with kolom_kiri:
        sumber = tampilkan_tabel(zip_artefak, "tabel_jumlah_data_per_sumber.csv",
                                 judul="Jumlah Data per Sumber")
        if sumber is not None and len(sumber.columns) >= 2:
            grafik_batang(sumber, sumber.columns[0], sumber.columns[1],
                          judul="Sebaran Data per Sumber")
    with kolom_kanan:
        tahun = tampilkan_tabel(zip_artefak, "tabel_jumlah_data_hasil_scraping_per_tahun.csv",
                                judul="Jumlah Data per Tahun")
        if tahun is not None and len(tahun.columns) >= 2:
            grafik_batang(tahun, tahun.columns[0], tahun.columns[1],
                          judul="Sebaran Data per Tahun", urutkan=False)

    st.divider()
    riwayat = tabel(zip_artefak, "riwayat_tahapan.csv", "tabel_rekapitulasi_praproses.csv")
    if riwayat is not None:
        st.markdown("**Corong Data pada Setiap Tahap Praproses**")
        kolom_tahap = kolom_pertama_cocok(riwayat, "Tahap")
        kolom_jumlah = kolom_pertama_cocok(riwayat, "Jumlah Data", "Jumlah")
        st.dataframe(riwayat, use_container_width=True, height=360)
        if kolom_tahap and kolom_jumlah:
            grafik_batang(riwayat, kolom_tahap, kolom_jumlah, mendatar=True,
                          urutkan=False, judul="Jumlah Data yang Tersisa per Tahap")
    else:
        pesan_kosong("tabel_rekapitulasi_praproses.csv")

    st.divider()
    tampilkan_tabel(zip_artefak, "tabel_contoh_transformasi.csv",
                    judul="Contoh Transformasi Teks per Tahap",
                    keterangan="Memperlihatkan perubahan satu ulasan dari teks mentah sampai siap model.",
                    tinggi=420)

    with st.expander("Corpus hasil praproses dan berkas pendukung"):
        tampilkan_tabel(zip_artefak, "data_preparation_final.csv",
                        judul="Corpus Hasil Praproses", tinggi=380)
        tampilkan_tabel(zip_artefak, "log_spelling_correction.csv",
                        judul="Log Koreksi Ejaan", tinggi=300)


# ---------------------------------------------------------------------------
# Halaman 3 - Corpus domain
# ---------------------------------------------------------------------------
def halaman_corpus(zip_artefak: Zip) -> None:
    st.subheader("Validasi Corpus Domain-Spesifik")

    tab_statistik, tab_indo4b, tab_istilah, tab_oov = st.tabs(
        ["Statistik corpus", "Perbandingan Indo4B", "Istilah domain", "OOV"])

    with tab_statistik:
        tampilkan_tabel(zip_artefak, "tabel_validasi_statistik_korpus.csv",
                        judul="Validasi Statistik Corpus")
        kolom_kiri, kolom_kanan = st.columns(2)
        with kolom_kiri:
            tampilkan_gambar(zip_artefak, "gambar_pertumbuhan_vocabulary.png")
        with kolom_kanan:
            tampilkan_gambar(zip_artefak, "gambar_wordcloud_korpus_keseluruhan.png")
        tampilkan_tabel(zip_artefak, "evaluasi_akhir_kualitas_korpus.csv",
                        judul="Evaluasi Akhir Kualitas Corpus")

    with tab_indo4b:
        tampilkan_tabel(zip_artefak, "tabel_perbandingan_corpus_ringkas.csv",
                        "tabel_perbandingan_korpus_indo4b.csv",
                        judul="Ringkasan Perbandingan Corpus terhadap Indo4B")
        tampilkan_gambar(zip_artefak, "gambar_perbandingan_corpus_domain_vs_indo4b.png",
                         "gambar_perbandingan_korpus_indo4b.png")
        tampilkan_tabel(zip_artefak, "tabel_cakupan_kelistrikan_indo4b.csv",
                        judul="Cakupan Istilah Kelistrikan pada Kedua Corpus")
        khas = tampilkan_tabel(zip_artefak, "tabel_istilah_khas_domain_vs_indo4b.csv",
                               "tabel_keyness_istilah_domain_indo4b.csv",
                               judul="Istilah Paling Khas berdasarkan Uji Log Likelihood",
                               tinggi=380)
        if khas is not None and len(khas.columns) >= 2:
            kolom_istilah = kolom_pertama_cocok(khas, "istilah", "kata", "token") or khas.columns[0]
            kolom_nilai = kolom_pertama_cocok(khas, "log likelihood", "keyness", "g2", "ll")
            if kolom_nilai:
                grafik_batang(khas, kolom_istilah, kolom_nilai, mendatar=True,
                              batas=20, judul="20 Istilah Paling Khas")

    with tab_istilah:
        kolom_kiri, kolom_kanan = st.columns(2)
        with kolom_kiri:
            tipe = tampilkan_tabel(zip_artefak, "tabel_distribusi_istilah_per_tipe.csv",
                                   judul="Distribusi Istilah per Tipe Entitas")
            if tipe is not None and len(tipe.columns) >= 2:
                grafik_batang(tipe, tipe.columns[0], tipe.columns[1])
        with kolom_kanan:
            kelas = tampilkan_tabel(zip_artefak, "tabel_distribusi_istilah_per_kelas.csv",
                                    judul="Distribusi Istilah per Kelas")
            if kelas is not None and len(kelas.columns) >= 2:
                grafik_batang(kelas, kelas.columns[0], kelas.columns[1])
        tampilkan_gambar(zip_artefak, "wordcloud_domain_kelistrikan.png")
        tampilkan_tabel(zip_artefak, "tabel_istilah_domain_teratas.csv",
                        judul="Istilah Domain Teratas", tinggi=360)
        tampilkan_tabel(zip_artefak, "tabel_cakupan_istilah_domain.csv",
                        judul="Cakupan Istilah Domain")

    with tab_oov:
        tampilkan_tabel(zip_artefak, "tabel_daftar_kata_oov.csv", "daftar_oov_indo4b.csv",
                        judul="Daftar Kata di Luar Kosakata", tinggi=460)
        tampilkan_tabel(zip_artefak, "tabel_istilah_belum_terwakili.csv",
                        judul="Istilah Domain yang Belum Terwakili", tinggi=300)


# ---------------------------------------------------------------------------
# Halaman 4 - Anotasi dan validasi pakar
# ---------------------------------------------------------------------------
def halaman_pakar(zip_artefak: Zip) -> None:
    st.subheader("Anotasi, Kesepakatan Pakar, dan Gold Standard")

    kappa = tabel(zip_artefak, "tabel_cohen_kappa.csv")
    if kappa is not None:
        kolom_aspek = kolom_pertama_cocok(kappa, "Aspek Dinilai", "Aspek")
        kolom_nilai = kolom_pertama_cocok(kappa, "Cohen Kappa", "kappa")
        if kolom_aspek and kolom_nilai:
            nilai = pd.to_numeric(kappa[kolom_nilai], errors="coerce")
            kartu_metrik([
                (str(a), format_angka(n, desimal=4), "Cohen Kappa antar pakar")
                for a, n in zip(kappa[kolom_aspek], nilai)
            ][:4])
            grafik_batang(kappa, kolom_aspek, kolom_nilai,
                          judul="Cohen Kappa Kesepakatan Antar Pakar")
        st.dataframe(kappa, use_container_width=True, hide_index=True)
    else:
        pesan_kosong("tabel_cohen_kappa.csv")

    st.divider()
    kolom_kiri, kolom_kanan = st.columns(2)
    with kolom_kiri:
        tampilkan_gambar(zip_artefak, "gambar_confusion_matrix_kesepakatan_pakar.png")
    with kolom_kanan:
        tampilkan_gambar(zip_artefak, "gambar_confusion_matrix_aturan_vs_pakar.png")

    st.divider()
    tampilkan_tabel(zip_artefak, "tabel_kesesuaian_aturan_vs_pakar.csv",
                    judul="Kesesuaian Aturan Entity Ruler dengan Anotasi Pakar")
    tampilkan_tabel(zip_artefak, "tabel_validasi_gold_ner_ulasan.csv",
                    judul="Validasi Gold Standard NER Tingkat Ulasan")

    with st.expander("Gold standard, sebaran, dan keterangan kode subclass"):
        tampilkan_tabel(zip_artefak, "gold_standard.csv", judul="Gold Standard Pakar", tinggi=360)
        tampilkan_tabel(zip_artefak, "tabel_sebaran_gold_ner_ulasan.csv",
                        judul="Sebaran Gold Standard NER")
        tampilkan_tabel(zip_artefak, "tabel_keterangan_kode_subclass.csv",
                        judul="Keterangan Kode Subclass", tinggi=360)
        tampilkan_tabel(zip_artefak, "daftar_ketidaksesuaian_aturan_vs_pakar.csv",
                        judul="Daftar Ketidaksesuaian Aturan dengan Pakar", tinggi=300)


# ---------------------------------------------------------------------------
# Halaman 5 - NER
# ---------------------------------------------------------------------------
def halaman_ner(zip_artefak: Zip) -> None:
    st.subheader("Modelling IndoBERT untuk Named Entity Recognition")

    banding = tabel(zip_artefak, "tabel_perbandingan_skema_ner.csv")
    if banding is not None:
        st.markdown("**Perbandingan Kinerja Dua Skema Pelabelan**")
        st.dataframe(banding, use_container_width=True, hide_index=True)
        kolom_skema = kolom_pertama_cocok(banding, "Skema")
        for metrik in ("Precision", "Recall", "F1 Score"):
            kolom_metrik = kolom_pertama_cocok(banding, metrik)
            if kolom_skema and kolom_metrik:
                grafik_batang(banding, kolom_skema, kolom_metrik, judul=metrik)

    st.divider()
    tab_subclass, tab_entity = st.tabs(["Skema kode subclass", "Skema tipe entitas"])
    for tab, skema in ((tab_subclass, "subclass"), (tab_entity, "entity")):
        with tab:
            tampilkan_tabel(zip_artefak, "laporan_seqeval_%s.csv" % skema,
                            judul="Laporan SeqEval Skema %s" % skema,
                            indeks_kolom_pertama=True, tinggi=420)
            kolom_kiri, kolom_kanan = st.columns(2)
            with kolom_kiri:
                tampilkan_gambar(zip_artefak, "gambar_matriks_prefiks_bio_%s.png" % skema)
            with kolom_kanan:
                tampilkan_gambar(zip_artefak, "gambar_matriks_BI_%s.png" % skema)
            tampilkan_tabel(zip_artefak, "riwayat_pelatihan_%s.csv" % skema,
                            judul="Riwayat Pelatihan Skema %s" % skema, tinggi=300)

    st.divider()
    st.markdown("### Distribusi Label BIO")
    kolom_kiri, kolom_kanan = st.columns(2)
    with kolom_kiri:
        sub = tampilkan_tabel(zip_artefak, "tabel_distribusi_bio_subclass.csv",
                              judul="Distribusi Label BIO Kode Subclass", tinggi=360)
        if sub is not None and len(sub.columns) >= 2:
            kolom_nilai = kolom_pertama_cocok(sub, "Jumlah", "frekuensi", "count")
            if kolom_nilai:
                grafik_batang(sub, sub.columns[0], kolom_nilai, mendatar=True, batas=15,
                              judul="15 Label Terbanyak")
    with kolom_kanan:
        ent = tampilkan_tabel(zip_artefak, "tabel_distribusi_bio_entitas.csv",
                              judul="Distribusi Label BIO Tipe Entitas", tinggi=360)
        if ent is not None and len(ent.columns) >= 2:
            kolom_nilai = kolom_pertama_cocok(ent, "Jumlah", "frekuensi", "count")
            if kolom_nilai:
                grafik_batang(ent, ent.columns[0], kolom_nilai, mendatar=True, batas=15,
                              judul="15 Label Terbanyak")

    with st.expander("Pembagian data dan pemeriksaan kebocoran"):
        tampilkan_tabel(zip_artefak, "tabel_pembagian_data_ner.csv",
                        judul="Pembagian Data Latih, Validasi, dan Uji")
        tampilkan_tabel(zip_artefak, "tabel_pencegahan_kebocoran_ner.csv",
                        judul="Pemeriksaan Pencegahan Kebocoran Data")

    with st.expander("Validasi model terhadap anotasi pakar"):
        tampilkan_tabel(zip_artefak, "tabel_kesesuaian_model_vs_pakar_ulasan.csv",
                        judul="Kesesuaian Model terhadap Pakar pada Satuan Ulasan")
        tampilkan_tabel(zip_artefak, "tabel_aturan_vs_model_ulasan.csv",
                        judul="Perbandingan Aturan dan Model")
        tampilkan_gambar(zip_artefak, "gambar_confusion_matrix_model_vs_pakar_ulasan.png")


# ---------------------------------------------------------------------------
# Halaman 6 - Sentimen
# ---------------------------------------------------------------------------
def halaman_sentimen(zip_artefak: Zip) -> None:
    st.subheader("Modelling IndoBERT untuk Analisis Sentimen")

    fold = tabel(zip_artefak, "tabel_hasil_per_fold.csv")
    if fold is not None:
        kolom_angka = [k for k in ("Accuracy", "F1 Macro", "F1 Weighted")
                       if kolom_pertama_cocok(fold, k)]
        kartu = []
        for nama in kolom_angka:
            kolom = kolom_pertama_cocok(fold, nama)
            nilai = pd.to_numeric(fold[kolom], errors="coerce").dropna()
            nilai = nilai[nilai <= 1.0001]
            if len(nilai):
                kartu.append((nama, format_angka(nilai.mean(), desimal=4),
                              "Rata-rata lima lipatan"))
        kartu_metrik(kartu)
        st.dataframe(fold, use_container_width=True, hide_index=True)

        kolom_fold = kolom_pertama_cocok(fold, "Fold", "Lipatan")
        kolom_macro = kolom_pertama_cocok(fold, "F1 Macro")
        if kolom_fold and kolom_macro:
            grafik_batang(fold, kolom_fold, kolom_macro, urutkan=False,
                          judul="Macro-F1 per Lipatan Validasi Silang")
    else:
        pesan_kosong("tabel_hasil_per_fold.csv")

    st.divider()
    kolom_kiri, kolom_kanan = st.columns(2)
    with kolom_kiri:
        tampilkan_tabel(zip_artefak, "classification_report_sentimen_akhir.csv",
                        judul="Classification Report Sentimen Gabungan",
                        indeks_kolom_pertama=True)
    with kolom_kanan:
        tampilkan_tabel(zip_artefak, "confusion_matrix_sentimen_akhir.csv",
                        judul="Confusion Matrix Sentimen Gabungan",
                        indeks_kolom_pertama=True)
        tampilkan_gambar(zip_artefak, "gambar_confusion_matrix_sentimen*.png")

    st.divider()
    st.markdown("### Corpus Final NER dan Sentimen")
    final = tabel(zip_artefak, "korpus_final_ner_sentimen.csv")
    if final is not None:
        kolom_sentimen = kolom_pertama_cocok(final, "sentimen")
        kolom_sumber = kolom_pertama_cocok(final, "sumber_label")
        kolom_kelas = kolom_pertama_cocok(final, "daftar_kelas")

        saring = st.multiselect(
            "Saring berdasarkan sentimen",
            options=sorted(final[kolom_sentimen].dropna().astype(str).unique()) if kolom_sentimen else [],
            default=[],
        )
        tampil = final
        if kolom_sentimen and saring:
            tampil = final[final[kolom_sentimen].astype(str).isin(saring)]

        kolom_a, kolom_b = st.columns(2)
        if kolom_sentimen:
            sebaran = (tampil[kolom_sentimen].astype(str).value_counts()
                       .rename_axis("Sentimen").reset_index(name="Jumlah"))
            with kolom_a:
                grafik_batang(sebaran, "Sentimen", "Jumlah",
                              judul="Distribusi Sentimen", warna=WARNA_SENTIMEN)
        if kolom_sumber:
            asal = (tampil[kolom_sumber].astype(str).value_counts()
                    .rename_axis("Asal Label").reset_index(name="Jumlah"))
            with kolom_b:
                grafik_batang(asal, "Asal Label", "Jumlah", judul="Asal Label")

        if kolom_kelas:
            pecah = (tampil[kolom_kelas].dropna().astype(str)
                     .str.split(",").explode().str.strip())
            pecah = pecah[pecah != ""]
            if len(pecah):
                kelas = (pecah.value_counts().rename_axis("Kelas")
                         .reset_index(name="Jumlah"))
                grafik_batang(kelas, "Kelas", "Jumlah", mendatar=True, batas=15,
                              judul="Kelas Pengaduan Terbanyak")

        st.dataframe(tampil.head(500), use_container_width=True, height=400)
        st.caption("Menampilkan %s dari %s baris."
                   % (format_angka(min(len(tampil), 500)), format_angka(len(tampil))))
        st.download_button("Unduh corpus final (CSV)",
                           data=tampil.to_csv(index=False).encode("utf-8"),
                           file_name="korpus_final_ner_sentimen.csv", mime="text/csv")
    else:
        pesan_kosong("korpus_final_ner_sentimen.csv")

    st.divider()
    st.markdown("### Word Cloud per Kelas Sentimen")
    gambar_wc = zip_artefak.daftar_gambar("gambar_wordcloud_sentimen_*.png")
    if gambar_wc:
        kolom = st.columns(min(3, len(gambar_wc)))
        for indeks, berkas in enumerate(gambar_wc):
            with kolom[indeks % len(kolom)]:
                st.image(str(berkas), caption=berkas.stem.split("_")[-1].upper(),
                         use_container_width=True)
    else:
        pesan_kosong("gambar_wordcloud_sentimen_*.png")

    with st.expander("Pseudo labeling dan tindak lanjut kelas netral"):
        tampilkan_tabel(zip_artefak, "evaluasi_ambang.csv", judul="Evaluasi Ambang Pseudo Labeling")
        tampilkan_tabel(zip_artefak, "kandidat_netral_untuk_pakar.csv",
                        judul="Kandidat Ulasan Netral untuk Validasi Pakar", tinggi=340)
        tampilkan_tabel(zip_artefak, "tabel_class_weight.csv", judul="Bobot Kelas")


# ---------------------------------------------------------------------------
# Halaman 7 - Prediksi langsung
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Memuat model NER...")
def muat_ner(sumber: str):
    return inferensi.muat_model_ner(sumber)


@st.cache_resource(show_spinner="Memuat model sentimen...")
def muat_sentimen(sumber: str):
    return inferensi.muat_model_sentimen(sumber)


@st.cache_data(show_spinner=False)
def muat_slang(jalur: str):
    return pemuat.muat_kamus_slang(jalur)


def halaman_prediksi(zip_artefak: Zip) -> None:
    st.subheader("Prediksi Langsung atas Ulasan Baru")
    st.caption("Model yang dipakai adalah model tersimpan hasil pelatihan notebook, "
               "tanpa pelatihan ulang.")

    tersedia, pesan = inferensi.pustaka_tersedia()
    if not tersedia:
        st.warning(
            "Pustaka torch dan transformers belum terpasang, sehingga halaman ini "
            "tidak aktif. Pasang dengan `pip install torch transformers` lalu muat "
            "ulang aplikasi. Halaman lain tetap dapat digunakan.\n\nDetail: %s" % pesan,
        )
        return

    model_tersedia = {n: p for n, p in zip_artefak.daftar_model().items() if p is not None}
    pilihan_ner = [n for n in model_tersedia if n.startswith("model_ner")]
    ada_sentimen = "model_sentimen_terbaik" in model_tersedia

    if not pilihan_ner and not ada_sentimen:
        st.info(
            "Folder model belum ditemukan. Salin folder `model/` hasil ekspor notebook "
            "ke samping app.py, atau isi repo Hugging Face pada kotak di bawah.",
        )

    with st.expander("Sumber model lanjutan (repo Hugging Face)"):
        repo_ner = st.text_input("Repo model NER", value="",
                                 placeholder="contoh: namaanda/pln-ner-subclass")
        repo_sentimen = st.text_input("Repo model sentimen", value="",
                                      placeholder="contoh: namaanda/pln-sentimen")

    kolom_kiri, kolom_kanan = st.columns(2)
    with kolom_kiri:
        skema = st.selectbox("Model NER", options=pilihan_ner or ["(tidak ada)"],
                             index=0, disabled=not pilihan_ner and not repo_ner)
    with kolom_kanan:
        pakai_praproses = st.toggle("Terapkan praproses seperti notebook", value=True)

    berkas_slang = zip_artefak.cari_tabel("Kamus SlangWord.xlsx", "kamus_slangword*")
    kamus = muat_slang(str(berkas_slang)) if berkas_slang else {}
    if berkas_slang:
        st.caption("Kamus kata tidak baku dimuat: %d entri." % len(kamus))

    teks = st.text_area(
        "Tulis atau tempelkan satu ulasan pengguna PLN Mobile",
        value="listrik saya padam sejak tadi malam dan token gagal masuk di aplikasi",
        height=120,
    )

    if not st.button("Jalankan prediksi", type="primary"):
        return

    teks_model = pemuat.bersihkan_teks(teks, kamus) if pakai_praproses else str(teks).strip()
    if not teks_model:
        st.error("Teks kosong setelah praproses. Coba ulasan lain.")
        return

    st.markdown("**Teks yang masuk ke model**")
    st.code(teks_model, language="text")

    kolom_ner, kolom_sentimen = st.columns(2)

    with kolom_ner:
        st.markdown("#### Entitas terdeteksi")
        sumber_ner = repo_ner.strip() or (str(model_tersedia.get(skema)) if skema in model_tersedia else "")
        if not sumber_ner:
            st.info("Model NER belum tersedia.")
        else:
            try:
                bungkus = muat_ner(sumber_ner)
                label_token = inferensi.prediksi_label_token(bungkus, teks_model)
                entitas = inferensi.gabung_entitas(label_token)
                if entitas:
                    st.dataframe(pd.DataFrame(entitas), use_container_width=True,
                                 hide_index=True)
                else:
                    st.warning("Tidak ada entitas yang terdeteksi pada ulasan ini.")
                with st.expander("Label BIO per token"):
                    st.dataframe(pd.DataFrame(label_token), use_container_width=True,
                                 hide_index=True)
            except Exception as galat:
                st.error("Gagal menjalankan model NER: %s" % galat)

    with kolom_sentimen:
        st.markdown("#### Sentimen")
        sumber_sentimen = repo_sentimen.strip() or (
            str(model_tersedia["model_sentimen_terbaik"]) if ada_sentimen else "")
        if not sumber_sentimen:
            st.info("Model sentimen belum tersedia.")
        else:
            try:
                bungkus = muat_sentimen(sumber_sentimen)
                peta = inferensi.peta_label_dari_ringkasan(zip_artefak.ringkasan)
                hasil = inferensi.prediksi_sentimen(bungkus, teks_model, peta)
                st.metric("Label", hasil["label"] or "-",
                          "keyakinan %s" % format_angka(hasil["keyakinan"], desimal=4),
                          delta_color="off")
                peluang = pd.DataFrame(sorted(hasil["peluang"].items(),
                                              key=lambda x: -x[1]),
                                       columns=["Kelas", "Peluang"])
                grafik_batang(peluang, "Kelas", "Peluang", warna=WARNA_SENTIMEN)
            except Exception as galat:
                st.error("Gagal menjalankan model sentimen: %s" % galat)


# ---------------------------------------------------------------------------
# Halaman 8 - Jelajah berkas
# ---------------------------------------------------------------------------
def halaman_berkas(zip_artefak: Zip) -> None:
    st.subheader("Jelajah Seluruh Tabel dan Gambar")

    kata_kunci = st.text_input("Cari nama atau judul berkas", value="")

    tab_tabel, tab_gambar = st.tabs(["Tabel", "Gambar"])

    with tab_tabel:
        daftar = zip_artefak.daftar_tabel()
        if kata_kunci:
            kunci = kata_kunci.lower()
            daftar = [b for b in daftar
                      if kunci in b.name.lower() or kunci in zip_artefak.judul(b.name).lower()]
        if not daftar:
            st.info("Tidak ada tabel yang cocok.")
        else:
            pilihan = st.selectbox(
                "Pilih tabel (%d berkas)" % len(daftar),
                options=daftar,
                format_func=lambda b: "%s  ·  %s" % (zip_artefak.judul(b.name), b.name),
            )
            bingkai = baca_tabel_cache(str(pilihan), False)
            if bingkai is None:
                st.error("Berkas tidak dapat dibaca.")
            else:
                st.caption("%s baris × %s kolom"
                           % (format_angka(len(bingkai)), format_angka(len(bingkai.columns))))
                st.dataframe(bingkai, use_container_width=True, height=480)
                st.download_button("Unduh berkas ini",
                                   data=bingkai.to_csv(index=False).encode("utf-8"),
                                   file_name=pilihan.name, mime="text/csv")

    with tab_gambar:
        gambar = zip_artefak.daftar_gambar()
        if kata_kunci:
            kunci = kata_kunci.lower()
            gambar = [b for b in gambar if kunci in b.name.lower()]
        if not gambar:
            st.info("Tidak ada gambar yang cocok.")
        else:
            kolom = st.columns(3)
            for indeks, berkas in enumerate(gambar):
                with kolom[indeks % 3]:
                    st.image(str(berkas), caption=berkas.name, use_container_width=True)

    st.divider()
    if st.button("Siapkan arsip ZIP seluruh tabel"):
        penampung = io.BytesIO()
        with zipfile.ZipFile(penampung, "w", zipfile.ZIP_DEFLATED) as arsip:
            for berkas in zip_artefak.daftar_tabel():
                arsip.write(berkas, arcname=berkas.name)
        st.download_button("Unduh semua tabel (ZIP)", data=penampung.getvalue(),
                           file_name="tabel_dashboard_pln.zip", mime="application/zip")


# ---------------------------------------------------------------------------
# Halaman awal ketika artefak belum ditemukan
# ---------------------------------------------------------------------------
def halaman_petunjuk() -> None:
    st.warning("Folder artefak belum ditemukan.")
    st.markdown(
        """
**Tiga langkah supaya dashboard tampil:**

1. Jalankan notebook `Thesis_Program_V28.ipynb` sampai sel **DASHBOARD 1 - EKSPOR
   ARTEFAK UNTUK DASHBOARD STREAMLIT**. Sel itu membuat folder
   `dashboard_corpus_pln/` di dalam Google Drive Anda.
2. Unduh folder `dashboard_corpus_pln/`, lalu letakkan **di samping `app.py`**
   sehingga strukturnya menjadi:

   ```text
   app.py
   pemuat.py
   inferensi.py
   dashboard_corpus_pln/
       data/
       gambar/
       model/
       manifest.json
       ringkasan.json
   ```
3. Isi kotak **Folder artefak** pada bilah sisi kiri dengan jalur folder itu,
   atau setel variabel lingkungan `PLN_DASHBOARD_DATA`.

Belum sempat mengekspor? Anda juga boleh mengisi kotak tersebut dengan folder
`Programming` yang memuat `output_preparation`, `output_ner_bio`,
`output_sentimen`, `output_visualisasi`, dan `output_modeling`. Dashboard akan
memindai berkasnya secara langsung.
        """
    )


# ---------------------------------------------------------------------------
# Program utama
# ---------------------------------------------------------------------------
def main() -> None:
    zip_artefak = bilah_sisi()
    if zip_artefak is None:
        tema.kepala_halaman("Halaman / Petunjuk pemasangan", JUDUL_APLIKASI,
                            LENCANA)
        st.caption(SUBJUDUL)
        halaman_petunjuk()
        return

    halaman = {
        "Ringkasan": halaman_ringkasan,
        "Data & Praproses": halaman_praproses,
        "Corpus Domain": halaman_corpus,
        "Validasi Pakar": halaman_pakar,
        "Model NER": halaman_ner,
        "Sentimen": halaman_sentimen,
        "Prediksi Langsung": halaman_prediksi,
        "Jelajah Berkas": halaman_berkas,
    }

    tempat_nav = _WADAH_NAV if _WADAH_NAV is not None else st.sidebar
    tempat_nav.markdown("<p class='pln-label-sisi'>Navigasi</p>",
                        unsafe_allow_html=True)
    pilihan = tempat_nav.radio("Halaman", list(halaman.keys()), index=0,
                               label_visibility="collapsed")

    tema.kepala_halaman("Dashboard / " + pilihan,
                        JUDUL_APLIKASI, LENCANA)
    halaman[pilihan](zip_artefak)


if __name__ == "__main__":
    main()
