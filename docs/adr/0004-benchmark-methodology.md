# ADR 0004 — Metodologi benchmark: workload key, warm-up, median

**Status:** accepted · 2026-11-19

## Context

Angka speedup/efficiency harus dipertanggungjawabkan di laporan. Crawling dipengaruhi cache OS,
latency loopback, ukuran halaman, jumlah proses, dan kondisi cluster. Tanpa kontrol, hasil mudah
menyesatkan (mis. run kedua selalu lebih cepat).

## Decision

1. **Workload key** — hash dari seed, maximum pages, depth, batch size, request timeout, dan
   versi bench site. Speedup hanya dihitung terhadap baseline sequential dengan key identik.
2. **Warm-up** — sebelum timer berjalan, runner menyentuh bench site sekali dan memanaskan
   process pool (submit parse dummy). Biaya spawn interpreter tidak ikut diukur.
3. **Median repeat** — setiap eksperimen dijalankan `repeat` kali (default 3) pada job baru, lalu
   diambil median execution time. Job baru penting karena frontier dedupe bersifat per job.
4. **Isolasi run** — hanya satu eksperimen aktif dalam satu waktu (409 untuk run lain).
5. **Distributed allowlist** — setiap job eksperimen mencantumkan worker yang diizinkan, sehingga
   uji N worker tidak terpengaruh worker lain di cluster.
6. **Sampling 1 s** — CPU/memory dicatat per detik dan dirata-rata; trace lengkap disimpan untuk
   grafik.

## Consequences

- Durasi eksperimen = repeat × waktu crawl. Untuk 120 halaman ≈ 2–5 s per run.
- Baseline harus dijalankan ulang jika perubahan kode mengubah `BENCH_VERSION`.
- Efficiency bisa >100% pada 1 worker karena setiap node menjalankan proses multiprocessing.
  Nilai ini dilaporkan apa adanya dengan catatan analisis.
- Bench site berada di Master, jadi CPU Master ikut terpakai. Untuk skenario jaringan nyata,
  jalankan worker di mesin terpisah dan catat kondisi jaringan di laporan.
