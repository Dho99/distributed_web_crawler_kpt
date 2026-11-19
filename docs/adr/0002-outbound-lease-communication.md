# ADR 0002 — Komunikasi outbound-only dengan model lease (pull)

**Status:** accepted · 2026-11-19

## Context

PRD menyebut komunikasi HTTP/WebSocket dua arah dan dispatcher Master → Worker. Di lab, komputer
worker sering berada di subnet berbeda, punya firewall default Windows, dan IP dinamis.

## Decision

Worker hanya melakukan koneksi keluar ke Master. Worker mengambil pekerjaan lewat
`POST /api/worker/lease` dengan jumlah slot kosong; Master membalas daftar task dan seketika
mengunci kapasitas worker tersebut.

## Rationale

- Master tidak perlu route ke Worker → tidak ada masalah NAT/firewall inbound.
- Lease adalah mekanisme backpressure alami: worker lambat otomatis mengambil lebih sedikit task.
- Reservasi kapasitas di Master (asyncio lock + transaksi) mencegah over-assignment.
- Model ini siap untuk dynamic load balancing karena setiap lease membawa kondisi resource terbaru.

## Consequences

- Latency dispatch mengikuti interval lease (default 1 s) — dapat diterima untuk crawling.
- Master harus tetap menyimpan lease deadline; worker yang mati tanpa mengirim hasil akan
  di-requeue oleh fault detector (Phase 5).
- Worker tetap membuka satu port HTTP (`/agent/info`) untuk onboarding manual dan health check,
  tetapi tidak pernah dipakai untuk dispatch task.
