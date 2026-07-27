"""Uji regresi: pastikan tidak ada grafik yang mengirim data biner ke Plotly.js.

LATAR BELAKANG
--------------
plotly (Python) >= 6.0 menyerialisasi array numpy / Series pandas menjadi
    {"dtype": "f8", "bdata": "<base64>"}
Plotly.js versi lama — termasuk yang dibundel Streamlit 1.31 — tidak mengenal
format itu. Yang berbahaya: **tidak ada pesan error sama sekali**. Grafik tetap
tampil, tapi Plotly.js diam-diam menggambar indeks (0, 1, 2, ...) sebagai ganti
nilainya. Garis omzet jadi rata di nol, heatmap jadi kosong.

Bug seperti ini hanya ketahuan kalau ada yang memperhatikan grafiknya aneh.
Script ini membuatnya ketahuan otomatis.

CARA KERJA
----------
Menjalankan setiap halaman lewat AppTest sambil menyadap st.plotly_chart,
lalu memeriksa JSON setiap figure. Kalau ada 'bdata', build dianggap gagal.

Pakai:  python scripts/check_charts.py
"""

import glob
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

TERTANGKAP = []
_asli = st.plotly_chart


def _sadap(figure_or_data, *a, **kw):
    TERTANGKAP.append(figure_or_data)
    return _asli(figure_or_data, *a, **kw)


st.plotly_chart = _sadap


def periksa_figure(fig, sumber, idx):
    """Kembalikan daftar masalah pada satu figure."""
    masalah = []
    try:
        payload = json.loads(fig.to_json())
    except Exception as e:
        return [f"{sumber} grafik #{idx}: gagal diserialisasi ({e})"]

    for i, trace in enumerate(payload.get("data", [])):
        for kunci in ("x", "y", "z", "values", "labels", "text"):
            nilai = trace.get(kunci)
            if isinstance(nilai, dict) and "bdata" in nilai:
                masalah.append(
                    f"{sumber} grafik #{idx} trace {i} ({trace.get('type')}): "
                    f"'{kunci}' terkirim sebagai biner {{bdata, dtype}} — "
                    f"Plotly.js lama akan menggambar indeks, bukan nilai. "
                    f"Bungkus dengan _v() / _v2() dari utils.charts.")

        # Trace kosong juga tanda ada yang salah
        if trace.get("type") in ("scatter", "bar"):
            y = trace.get("y")
            if isinstance(y, list) and len(y) == 0:
                masalah.append(f"{sumber} grafik #{idx} trace {i}: sumbu y kosong")
    return masalah


def main():
    halaman = ["app.py"] + [f for f in sorted(glob.glob(str(ROOT / "pages" / "*.py")))
                            if "__init__" not in f]
    semua_masalah, total = [], 0

    for h in halaman:
        nama = Path(h).name
        TERTANGKAP.clear()
        at = AppTest.from_file(h, default_timeout=200)
        try:
            at.run()
        except Exception as e:
            semua_masalah.append(f"{nama}: halaman gagal dijalankan — {e}")
            continue
        if at.exception:
            for ex in at.exception:
                semua_masalah.append(f"{nama}: {ex.value}")
            continue

        for i, fig in enumerate(TERTANGKAP, 1):
            semua_masalah.extend(periksa_figure(fig, nama, i))
        total += len(TERTANGKAP)
        print(f"  {nama:<34} {len(TERTANGKAP):>2} grafik diperiksa")

    print(f"\nTotal {total} grafik dari {len(halaman)} halaman.")
    if semua_masalah:
        print(f"\n{len(semua_masalah)} MASALAH DITEMUKAN:\n")
        for m in semua_masalah:
            print(f"  x {m}")
        sys.exit(1)
    print("\nOK — semua data grafik terkirim sebagai array JSON biasa.")


if __name__ == "__main__":
    main()
