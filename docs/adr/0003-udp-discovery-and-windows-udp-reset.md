# ADR 0003 — Discovery via UDP broadcast + fallback manual

**Status:** accepted · 2026-11-19

## Context

PRD meminta node discovery otomatis dari GUI, dengan fallback pairing token dan add-by-IP.

## Decision

- Master mengirim probe UDP broadcast ke port `5599` saat tombol SCAN NETWORK ditekan.
- Worker Agent mendengarkan port tersebut dan membalas informasi hardware secara unicast.
- Fallback: `POST /api/nodes/manual` memanggil `GET /agent/info` worker dengan pairing token.

## Rationale

- Tidak butuh mDNS/zeroconf dependency, deterministik, mudah dijelaskan di laporan.
- Scan bersifat on-demand (bukan periodic broadcast) sehingga lalu lintas LAN minimal.
- Balasan agent berisi `cluster_id`; GUI dapat menandai node dari cluster lain.

## Consequences

- Broadcast dapat diblokir kebijakan jaringan → fallback manual wajib dipertahankan.
- Beberapa agent di satu mesin harus berbagi port `5599`; SO_REUSEADDR dipakai, tetapi untuk
  skenario multi-agent per host sebaiknya satu port per instance (`--discovery-port`).
- Windows: ICMP port-unreachable dapat mematikan socket UDP penerima. Karena itu
  `SIO_UDP_CONNRESET` dimatikan via `WSAIoctl`
  (`shared/netinfo.py:disable_udp_connreset`). Tanpa ini listener berhenti membalas setelah
  probe pertama yang port-nya sudah ditutup.
