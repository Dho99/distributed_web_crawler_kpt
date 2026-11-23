# Daftar Input yang Diperlukan

Dokumen ini mencatat data yang belum tersedia saat draft dibuat. Placeholder pada laporan tidak boleh diganti dengan angka asumsi.

## Prioritas tinggi

| No. | Input | Dipakai di | Kondisi | Tindakan |
|---:|---|---|---|---|
| 1 | Inventaris 10 node fisik: hostname, IP, OS, CPU, RAM, peran | Tabel 3.6, 3.7 | `[PERLU DATA]` | Isi dari inventaris laboratorium |
| 2 | CSV benchmark 1/2/4/6/9 Worker | Tabel 4.4 | `[BELUM DIUJI]` | Jalankan protokol benchmark, export CSV |
| 3 | CSV sequential dan local parallel | Tabel 4.2, 4.3 | `[BELUM DIUJI]` | Jalankan baseline dan local parallel |
| 4 | Log fault tolerance: waktu gagal, deteksi, requeue, recovery | Tabel 4.7 | `[BELUM DIUJI]` | Simulasikan kegagalan, simpan log |
| 5 | Screenshot cluster 9 Worker | Bagian 4.1.6, AC-04 | `[MASUKKAN SCREENSHOT]` | Ambil screenshot setelah 9 Worker aktif |
| 6 | Bukti multiprocessing per Worker | AC-07 | Sebagian dari kode | Screenshot child process / metrics |
| 7 | Format laporan resmi kampus | Seluruh dokumen | `[PERLU DATA]` | Sesuaikan margin, font, cover, sitasi |

## Prioritas sedang

| No. | Input | Dipakai di | Kondisi | Tindakan |
|---:|---|---|---|---|
| 8 | Nama, NIM, program studi, institusi | Cover | `[PERLU DATA]` | Isi data penyusun |
| 9 | Kondisi jaringan: media, subnet, gateway, firewall, DNS | Tabel 3.7 | `[PERLU DATA]` | Catat saat hari-H |
| 10 | Referensi akademik tambahan | BAB II | `[PERLU REFERENSI]` | Tambah jurnal/buku yang relevan |
| 11 | Data CPU/memory per Worker | Tabel 4.5 | `[BELUM DIUJI]` | Export dari `worker_metrics` |
| 12 | Data static vs dynamic scheduling | Tabel 4.6 | `[BELUM DIUJI]` | Jalankan dua konfigurasi dengan workload sama |

## Data yang sudah tersedia

| Data | Nilai | Sumber |
|---|---|---|
| Master hostname | FCM-LOQ | `data/crawlmesh.db` |
| Master IP | 192.168.18.141 | `.env.example`, database |
| Master OS | Windows 11 | database |
| Master CPU | 16 core | database |
| Master RAM | 21.144.231.936 byte | database |
| Python | 3.15.2 | runtime |
| Jumlah screenshot UI | 14 gambar | `docs/guides/img/` |
| Jumlah experiment di DB | 0 | `data/crawlmesh.db` |

## Aturan pengisian

1. Jangan mengisi `[BELUM DIUJI]` dengan angka simulasi.
2. Setiap angka pada BAB IV harus punya sumber: CSV, database, atau log.
3. Speedup hanya dihitung terhadap baseline sequential dengan `workload_key` sama.
4. Efficiency memakai jumlah process/Worker yang benar.
5. Recovery time hanya diisi jika timestamp deteksi dan timestamp pemulihan tersedia.
6. Setelah data diisi, jalankan ulang `build_report.py`, `export_pdf.ps1`, dan `qa_check.py`.
