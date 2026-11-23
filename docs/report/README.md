# Draft Laporan CrawlMesh

Workspace penyusunan `Laporan_Proyek_CrawlMesh_Draft.docx`.

## Output

| File | Keterangan |
|---|---|
| `Laporan_Proyek_CrawlMesh_Draft.docx` | draft utama, editable |
| `Laporan_Proyek_CrawlMesh_Draft.pdf` | hasil export Word untuk QA |
| `qa-report.md` | hasil pemeriksaan struktur dan format |
| `missing-inputs.md` | data yang masih diperlukan |
| `report.md` | sumber isi laporan (Markdown + LaTeX) |
| `template.docx` | reference document Pandoc |
| `figures/` | diagram dan HTML sumber Mermaid |
| `data/` | tempat CSV benchmark bila tersedia |

Salinan draft juga ditulis ke root repository:

```text
Laporan_Proyek_CrawlMesh_Draft.docx
```

## Format

- A4, margin kiri 4 cm, kanan/atas/bawah 3 cm.
- Times New Roman **11 pt**, spasi 1,5, justify.
- Heading 1 14 pt, Heading 2 12 pt, Heading 3 11 pt.
- Caption tabel/gambar 10 pt.
- Tabel 7,5–9 pt agar muat di halaman portrait.
- Daftar isi otomatis (field TOC) dan nomor halaman footer.
- Persamaan memakai OMML native Word, bukan gambar.

## Build

Prasyarat: Python 3.12+, Microsoft Word (untuk update TOC dan export PDF).

```powershell
# tool laporan (sudah diinstal di .venv proyek)
.\.venv\Scripts\python.exe -m pip install python-docx pypandoc-binary latex2mathml lxml pymupdf

# 1) buat reference document
.\.venv\Scripts\python.exe docs\report\make_template.py

# 2) render diagram Mermaid ke PNG
.\.venv\Scripts\python.exe docs\report\render_figures.py

# 3) build DOCX
.\.venv\Scripts\python.exe docs\report\build_report.py

# 4) update TOC, simpan DOCX, export PDF
powershell -ExecutionPolicy Bypass -File docs\report\export_pdf.ps1

# 5) QA struktur
.\.venv\Scripts\python.exe docs\report\qa_check.py
```

## Pipeline rumus

Sumber rumus memakai LaTeX kanonik:

```latex
$$
S = \frac{T_{\text{seq}}}{T_{\text{par}}}
\qquad (3.2)
$$
```

Pandoc mengubah LaTeX menjadi OMML native Word. Jangan memakai escaping Markdown seperti `\\[`, `\\(`, atau `\_` di dalam math. Jangan mengganti persamaan dengan gambar.

## Data

Isi `data/` dengan CSV hasil benchmark bila tersedia. Skema minimal:

```text
experiment_type,worker_count,scheduling_mode,execution_time_ms,pages_ok,
pages_failed,speedup,efficiency,throughput,cpu_avg,mem_avg,workload_key
```

Tanpa CSV, tabel pengukuran di BAB IV tetap memakai placeholder `[BELUM DIUJI]`. Jangan mengisi angka fiktif.

## Batas draft

- BAB III disusun lengkap.
- BAB IV bagian implementasi lengkap; bagian pengukuran memakai placeholder.
- BAB I, II, dan V masih outline.
- Validasi 9 Worker dan 10 node fisik belum tersedia.
- `failure_events` belum diisi kode, sehingga recovery time belum terstruktur.
