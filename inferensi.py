"""Inferensi model IndoBERT untuk halaman Prediksi Langsung.

Berkas ini tidak melatih apa pun. Model NER dan model sentimen yang sudah
disimpan notebook pada BAGIAN 5 dan BAGIAN 8 hanya dimuat kembali, lalu
dipakai untuk memberi ramalan atas satu ulasan baru. Impor torch dan
transformers dilakukan di dalam fungsi supaya dashboard tetap dapat dibuka
meskipun kedua pustaka berat itu belum terpasang.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

URUTAN_LABEL_SENTIMEN = ["NEGATIF", "NETRAL", "POSITIF"]
MAKS_PANJANG = 128


class PustakaBelumAda(RuntimeError):
    """Ditandai ketika torch atau transformers belum terpasang."""


def pustaka_tersedia() -> Tuple[bool, str]:
    """Memeriksa ketersediaan torch dan transformers."""
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except Exception as galat:  # pragma: no cover - bergantung lingkungan
        return False, str(galat)
    return True, ""


def _perangkat():
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def _muat(kelas_model, sumber: str) -> dict:
    """Memuat tokenizer dan model dari folder lokal atau repo Hugging Face."""
    tersedia, pesan = pustaka_tersedia()
    if not tersedia:
        raise PustakaBelumAda(pesan)

    import torch
    from transformers import AutoTokenizer

    sumber = str(sumber)
    tokenizer = AutoTokenizer.from_pretrained(sumber)
    model = kelas_model.from_pretrained(sumber)
    perangkat = _perangkat()
    model.to(perangkat)
    model.eval()
    id2label = {int(k): str(v) for k, v in (model.config.id2label or {}).items()}
    return {
        "tokenizer": tokenizer,
        "model": model,
        "perangkat": perangkat,
        "id2label": id2label,
        "sumber": sumber,
        "torch": torch,
    }


def muat_model_ner(sumber) -> dict:
    """Memuat model klasifikasi token (NER skema subclass atau entity)."""
    from transformers import AutoModelForTokenClassification

    return _muat(AutoModelForTokenClassification, sumber)


def muat_model_sentimen(sumber) -> dict:
    """Memuat model klasifikasi kalimat untuk analisis sentimen."""
    from transformers import AutoModelForSequenceClassification

    return _muat(AutoModelForSequenceClassification, sumber)


# ----------------------------------------------------------------------------
# Prediksi NER
# ----------------------------------------------------------------------------
def prediksi_label_token(bungkus: dict, teks: str) -> List[Dict[str, str]]:
    """Mengembalikan pasangan token dan label BIO untuk satu ulasan.

    Cara pemetaan label mengikuti notebook: teks dipecah berdasarkan spasi,
    tokenizer dijalankan dengan is_split_into_words, lalu label diambil dari
    subword pertama setiap kata.
    """
    token = str(teks or "").split()
    if not token:
        return []

    torch = bungkus["torch"]
    tokenizer = bungkus["tokenizer"]
    sandi = tokenizer(token, is_split_into_words=True, truncation=True,
                      max_length=MAKS_PANJANG, return_tensors="pt")
    sandi_perangkat = {k: v.to(bungkus["perangkat"]) for k, v in sandi.items()}
    with torch.no_grad():
        logit = bungkus["model"](**sandi_perangkat).logits
    tebak = logit.argmax(-1)[0].tolist()
    peluang = torch.softmax(logit, dim=-1)[0].max(-1).values.tolist()

    word_ids = tokenizer(token, is_split_into_words=True, truncation=True,
                         max_length=MAKS_PANJANG).word_ids()
    id2label = bungkus["id2label"]
    per_kata: Dict[int, Tuple[str, float]] = {}
    for posisi, kata in enumerate(word_ids):
        if kata is None or kata in per_kata:
            continue
        per_kata[kata] = (id2label.get(int(tebak[posisi]), "O"),
                          float(peluang[posisi]))

    hasil = []
    for i, kata in enumerate(token):
        label, yakin = per_kata.get(i, ("O", 0.0))
        hasil.append({"token": kata, "label": label, "keyakinan": round(yakin, 4)})
    return hasil


def gabung_entitas(label_token: List[Dict[str, str]]) -> List[Dict[str, object]]:
    """Menggabungkan urutan label B- dan I- menjadi entitas utuh."""
    entitas: List[Dict[str, object]] = []
    kini: Optional[Dict[str, object]] = None
    for posisi, baris in enumerate(label_token):
        label = str(baris.get("label", "O"))
        if label == "O" or "-" not in label:
            kini = None
            continue
        awalan, jenis = label.split("-", 1)
        if awalan.upper() == "B" or kini is None or kini["jenis"] != jenis:
            kini = {"jenis": jenis, "token": [baris["token"]],
                    "mulai": posisi, "keyakinan": [baris.get("keyakinan", 0.0)]}
            entitas.append(kini)
        else:
            kini["token"].append(baris["token"])
            kini["keyakinan"].append(baris.get("keyakinan", 0.0))

    rapi = []
    for baris in entitas:
        keyakinan = baris["keyakinan"] or [0.0]
        rapi.append({
            "Entitas": " ".join(baris["token"]),
            "Jenis": baris["jenis"],
            "Posisi Token": int(baris["mulai"]) + 1,
            "Rata Keyakinan": round(sum(keyakinan) / len(keyakinan), 4),
        })
    return rapi


# ----------------------------------------------------------------------------
# Prediksi sentimen
# ----------------------------------------------------------------------------
def _nama_label_sentimen(bungkus: dict, peta_cadangan: Optional[Dict[int, str]] = None) -> Dict[int, str]:
    """Menentukan nama kelas sentimen, dengan cadangan bila config generik."""
    id2label = dict(bungkus.get("id2label") or {})
    generik = all(str(v).upper().startswith("LABEL_") for v in id2label.values()) if id2label else True
    if not generik:
        return id2label
    if peta_cadangan:
        return dict(peta_cadangan)
    jumlah = len(id2label) or len(URUTAN_LABEL_SENTIMEN)
    return {i: URUTAN_LABEL_SENTIMEN[i] if i < len(URUTAN_LABEL_SENTIMEN) else "KELAS %d" % i
            for i in range(jumlah)}


def prediksi_sentimen(bungkus: dict, teks: str,
                      peta_label: Optional[Dict[int, str]] = None) -> Dict[str, object]:
    """Mengembalikan label sentimen beserta peluang tiap kelas."""
    isi = str(teks or "").strip()
    if not isi:
        return {"label": None, "keyakinan": 0.0, "peluang": {}}

    torch = bungkus["torch"]
    tokenizer = bungkus["tokenizer"]
    sandi = tokenizer(isi, truncation=True, max_length=MAKS_PANJANG,
                      return_tensors="pt")
    sandi = {k: v.to(bungkus["perangkat"]) for k, v in sandi.items()}
    with torch.no_grad():
        logit = bungkus["model"](**sandi).logits
    peluang = torch.softmax(logit, dim=-1)[0].tolist()

    nama = _nama_label_sentimen(bungkus, peta_label)
    sebaran = {nama.get(i, "KELAS %d" % i): round(float(p), 4)
               for i, p in enumerate(peluang)}
    terpilih = max(range(len(peluang)), key=lambda i: peluang[i])
    return {
        "label": nama.get(terpilih, "KELAS %d" % terpilih),
        "keyakinan": round(float(peluang[terpilih]), 4),
        "peluang": sebaran,
    }


def peta_label_dari_ringkasan(ringkasan: dict) -> Optional[Dict[int, str]]:
    """Membaca LABEL2ID hasil ekspor notebook menjadi peta id ke nama."""
    try:
        mentah = ((ringkasan or {}).get("model") or {}).get("label_sentimen") or {}
        peta = {int(v): str(k) for k, v in mentah.items()}
        return peta or None
    except (TypeError, ValueError):
        return None


def ukuran_folder_mb(folder) -> float:
    """Menghitung ukuran sebuah folder model dalam megabita."""
    folder = Path(folder)
    if not folder.exists():
        return 0.0
    total = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
    return round(total / 1024 ** 2, 1)
