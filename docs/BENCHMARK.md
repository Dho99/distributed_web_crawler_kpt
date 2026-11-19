# Protokol Benchmark (untuk BAB IV)

Dokumen ini adalah prosedur pengambilan data agar hasil UAS dapat dibandingkan dan direproduksi.
Semua langkah dilakukan dari GUI, tanpa mengubah kode.

---

## 1. Persiapan

1. Pastikan Master dan seluruh Worker memakai build yang sama (commit yang sama).
2. Pastikan **bench version** tidak berubah selama satu sesi pengukuran
   (`BENCH_VERSION` di `master/app/domain/jobs.py`).
3. Catat hardware setiap node: hostname, CPU core, RAM, OS, koneksi (kabel/Wi-Fi).
4. Catat konfigurasi worker: `--pool-size` (disarankan core fisik − 1, maksimum 6).
5. Pastikan cluster idle: tidak ada crawl job lain berjalan, tidak ada eksperimen aktif.
6. Tutup aplikasi berat di Master (bench site di-serve Master).

Tabel hardware (isi sebelum pengukuran):

| Node | Hostname | CPU core | RAM | OS | Pool | Koneksi |
|------|----------|----------|-----|----|------|---------|
| M | | | | | — | |
| W1 | | | | | | |
| … | | | | | | |

---

## 2. Parameter tetap

Semua run pada satu sesi memakai nilai berikut (jangan diubah antar-run):

| Parameter | Nilai |
|-----------|-------|
| Seed | `http://<MASTER_IP>:8000/bench/` |
| Maximum pages | 120 |
| Maximum depth | 2 |
| Batch size | 5 |
| Request timeout | 10 s |
| Domain delay | 0 s |
| Scheduling | dynamic (default) |
| Repeat | 3 (median) |

`workload_key` akan sama untuk semua tipe selama parameter di atas identik.

---

## 3. Urutan pengambilan data

1. **Sequential** — Performance Lab → tipe `Sequential` → RUN. Catat execution time.
2. **Local parallel** — tipe `Local parallel`, workers = 4 → RUN.
3. **Distributed** — aktifkan N worker sesuai skenario, lalu tipe `Distributed`,
   workers = N → RUN.
4. **Scalability suite** — tipe `Scalability` → RUN. Runner menjalankan baseline (jika belum ada)
   dan langkah 1, 2, 4, 6, 9 worker; langkah yang melebihi worker aktif dilewati.
5. **Static vs dynamic** — ulangi Distributed dengan `scheduling = static`, bandingkan distribusi
   task di Task Monitor dan execution time.
6. **Fault tolerance** — jalankan Crawl Job (bukan benchmark), lalu matikan satu worker di tengah
   crawl. Catat task requeue dan waktu sampai job selesai; lihat Task Monitor + Activity.

---

## 4. Data yang harus dicatat

Export CSV dari **Performance Lab / Experiment History**, lalu isi tabel:

| Experiment | Workers | Exec (s) | Speedup | Efficiency | Throughput | CPU avg | MEM avg |
|------------|---------|----------|---------|------------|------------|---------|---------|
| Sequential | 1 proc | | 1.00 | 100% | | | |
| Local parallel | 4 proc | | | | | | |
| Distributed | 1 | | | | | | |
| Distributed | 2 | | | | | | |
| Distributed | 4 | | | | | | |
| Distributed | 6 | | | | | | |
| Distributed | 9 | | | | | | |

Fault tolerance:

| Metrik | Nilai |
|--------|-------|
| Worker disimulasikan | |
| Waktu deteksi (heartbeat → offline) | |
| Task terdampak | |
| Task requeued | |
| Worker pengganti | |
| Recovery time (deteksi → task selesai) | |

Rumus:

```
Speedup    S = T_sequential / T_parallel
Efficiency E = (S / N) × 100%
Throughput   = successful_pages / execution_time
Recovery     = task_selesai − failure_detection
```

---

## 5. Interpretasi yang harus ditulis di laporan

- **Efficiency turun** saat worker bertambah adalah normal: overhead koordinasi, network, dan
  kontensi SQLite Master ikut naik.
- **Efficiency > 100% pada N=1** berarti satu node menjalankan beberapa proses parsing
  (multiprocessing). Jelaskan sebagai kontribusi proses per node, bukan kesalahan hitung.
- Bandingkan **distributed vs sequential**, bukan distributed vs local parallel, untuk klaim
  speedup sistem terdistribusi.
- Pisahkan pengaruh jaringan: sebutkan topologi, switch/AP, dan apakah worker berada di mesin
  berbeda.
- Jika hasil antar-ulangan berbeda jauh, ulangi sesi dan catat variansi (median sudah dipakai,
  tetapi kondisi jaringan bisa berubah).

---

## 6. Batasan yang jujur

- Bench site berada di Master → request worker menuju Master, sehingga CPU Master ikut bekerja.
- SQLite membatasi throughput tulis (±50 task/detik); cukup untuk skala UAS.
- Clock skew diminimalkan karena semua durasi dihitung dari timestamp Master.
- Satu Master tanpa HA (sesuai batasan PRD).
