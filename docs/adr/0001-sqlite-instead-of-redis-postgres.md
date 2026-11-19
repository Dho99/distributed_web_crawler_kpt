# ADR 0001 — SQLite sebagai queue dan store, tanpa Redis/PostgreSQL

**Status:** accepted · 2026-11-19

## Context

PRD merekomendasikan Redis (task queue) dan PostgreSQL (storage). Target demo adalah 10 komputer
fisik di lab dengan OS campuran Windows/Linux, waktu setup terbatas, dan volume maksimum sekitar
1.000 halaman per eksperimen.

## Decision

Gunakan satu file SQLite (WAL mode, `busy_timeout=5s`) di Master untuk seluruh state: cluster,
frontier, task, hasil, metrik, eksperimen.

## Rationale

- Nol infrastruktur tambahan: tidak ada server Redis/PostgreSQL yang harus hidup di lab.
- Volume UAS jauh di bawah batas praktis SQLite untuk pola kerja ini.
- Satu proses penulis (asyncio + lock) menghilangkan `database is locked`.
- Backup/export cukup menyalin satu file; memudahkan lampiran laporan.

## Consequences

- Throughput tulis praktis ±50 task/detik — cukup untuk 9 worker dengan batch kecil, tidak untuk
  skala produksi.
- Tidak ada pub/sub bawaan; fan-out realtime memakai hub WebSocket in-process.
- Kalau skala naik, kontrak repositori cukup dipindah ke PostgreSQL + Redis tanpa mengubah domain
  layer (semua akses DB terpusat di `master/app/db`).
