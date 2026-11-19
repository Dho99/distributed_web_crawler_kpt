# CrawlMesh

Distributed web crawler dengan orkestrasi Master–Worker lewat GUI. Tugas UAS Komputasi Paralel
dan Sistem Terdistribusi — Tema 8 (Distributed Web Crawler).

- **Master** — FastAPI + SQLite: cluster registry, scheduler, dashboard, WebSocket event stream.
- **Worker Agent** — agent ringan per komputer: registrasi, heartbeat, multiprocessing pool.
- **Web GUI** — React + TypeScript + Tailwind, di-serve langsung oleh Master (satu port).

Status implementasi: **Phase 0–6 selesai** — cluster lifecycle, discovery, heartbeat, role
assignment, fault detection + requeue, distributed crawl engine (frontier → task → lease →
fetch/parse → aggregation), multiprocessing parser pool, dynamic/static scheduling, bench site,
dan Performance Lab dengan experiment history otomatis.

---

## Quick start

Prasyarat: Python 3.12+, Node.js 20+, dua mesin di LAN yang sama untuk uji distributed.

```powershell
# 1) dependencies
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd web; npm install; cd ..

# 2) build GUI (output ke master/app/static)
cd web; npm run build; cd ..

# 3) jalankan Master
.\scripts\run_master.ps1
#    GUI  : http://127.0.0.1:8000
#    API  : http://127.0.0.1:8000/docs
```

Buka GUI, tekan **Initialize this node as master**, lalu salin pairing token dari halaman
**Settings**.

Di setiap komputer Worker:

```powershell
# salin repo + .venv, lalu:
.\scripts\run_worker.ps1 -Master http://192.168.18.141:8000 -Token '<PAIRING_TOKEN>' -PoolSize 4
```

Kembali ke GUI → **Node Discovery** → **SCAN NETWORK** → **ASSIGN AS WORKER**.
Worker yang sudah di-assign akan mengirim heartbeat dan tampil di **Overview** / **Cluster**.

### Jalankan crawl pertama

**Crawl Jobs** → isi seed URL → **START CRAWLING**.

Default seed `http://127.0.0.1:8000/bench/` menunjuk bench site statis yang di-serve Master
(300 halaman deterministik, ±120 KB per halaman) sehingga benchmark tidak bergantung internet.
Gunakan `http://<MASTER_IP>:8000/bench/` jika worker berada di komputer lain — host bench
otomatis diizinkan menembus SSRF guard untuk job ini.

Halaman **Task Monitor** menampilkan lease per worker, **Results** menampilkan agregasi hasil
dengan filter dan export CSV/JSON.

### Jalankan benchmark

**Performance Lab** → pilih tipe eksperimen:

| Tipe | Arti |
|------|------|
| Sequential | 1 proses di Master, baseline pembanding |
| Local parallel | Master menjalankan N proses parser (multiprocessing) |
| Distributed | job didistribusikan ke N worker aktif (allowlist per eksperimen) |
| Scalability | otomatis menjalankan baseline + 1/2/4/6/9 worker (langkah yang melebihi jumlah worker dilewati) |

Setiap run diulang `repeat` kali (default 3) dan diambil median. Hasil tersimpan di
**Experiment History** lengkap dengan speedup, efficiency, throughput, CPU/memory, dan
trace resource per detik. Export CSV/JSON tersedia di kedua halaman.

Baseline sequential memakai `workload_key` yang sama (seed, pages, depth, batch, timeout), jadi
speedup hanya dibandingkan dengan beban yang setara.

Mode pengembangan (hot reload): `.\scripts\dev.ps1` menjalankan uvicorn `--reload` + Vite dev server
di `http://127.0.0.1:5173` dengan proxy ke `:8000`.

---

## Arsitektur

```
Browser (GUI) ──HTTP/WS──> Master (FastAPI, :8000) ──SQLite── data/crawlmesh.db
                                ▲
                                │ worker → master (HTTP, outbound only)
                                │ register · heartbeat · lease · result
                    ┌───────────┼───────────┐
                Worker 1    Worker 2    Worker N
                (agent+pool)(agent+pool)(agent+pool)
```

Keputusan penting:

- **Worker tidak membuka port inbound untuk task.** Semua dispatch memakai lease pull
  (`POST /api/worker/lease`), jadi firewall lab dan subnet berbeda tidak jadi masalah.
- **Discovery** memakai UDP broadcast ke port `5599` (tombol SCAN NETWORK) + fallback
  add-by-IP untuk lintas subnet.
- **Role assignment eksplisit.** Agent yang hidup hanya berstatus `pending`; operator menekan
  ASSIGN AS WORKER untuk mengaktifkannya. Satu cluster = satu Master.
- **SQLite (WAL)** sebagai queue + store, tanpa Redis/PostgreSQL. Rasional ada di
  [`docs/adr/0001-sqlite-instead-of-redis-postgres.md`](docs/adr/0001-sqlite-instead-of-redis-postgres.md).

### Port

| Port | Proto | Sisi | Fungsi |
|------|-------|------|--------|
| 8000 | TCP | Master | GUI, REST API, WebSocket `/ws` |
| 5599 | UDP | Worker | discovery listener (broadcast probe dari Master) |
| 8010 | TCP | Worker | onboarding (`/agent/info`), health |

---

## Struktur repo

```
shared/       model Pydantic + normalisasi URL + deteksi IP LAN
master/       FastAPI app, domain services, SQLite schema, static GUI build
worker/       agent heartbeat/lease loop, resource monitor, discovery listener
web/          React + TS + Tailwind + Recharts
scripts/      run_master / run_worker / dev / install agent (Windows & Linux)
tests/        pytest (urlnorm + cluster lifecycle)
docs/         TDD, API, ADR, runbook 10 node
```

## API singkat

| Method | Path | Keterangan |
|--------|------|------------|
| POST | `/api/cluster/init` | inisialisasi Master, buat cluster id + token |
| POST | `/api/cluster/discover` | scan UDP, daftar agent yang merespons |
| GET | `/api/cluster/overview` | snapshot dashboard |
| POST | `/api/nodes/manual` | registrasi agent lintas subnet |
| POST | `/api/nodes/{id}/assign` | aktifkan worker |
| POST | `/api/nodes/{id}/simulate-failure` | simulasi kegagalan (status bertahan) |
| POST | `/api/nodes/{id}/recover` | pulihkan worker tersimulasi |
| POST | `/api/jobs` | buat crawl job + seed frontier, langsung running |
| GET | `/api/jobs` | daftar job + agregat progres |
| POST | `/api/jobs/{id}/pause\|resume\|cancel` | kontrol lifecycle job |
| GET | `/api/tasks` | ledger task, filter job/status/worker |
| GET | `/api/results` | hasil crawl dengan filter + pagination |
| GET | `/api/results/export?format=csv\|json` | export hasil |
| GET | `/api/jobs/{id}/frontier` | hitungan state frontier |
| GET | `/api/metrics/timeseries` | time series resource worker |
| POST | `/api/experiments/run` | jalankan benchmark (sequential/local/distributed/scalability) |
| GET | `/api/experiments` | riwayat eksperimen + filter `group_id` |
| GET | `/api/experiments/{id}?samples=true` | detail + sampel resource |
| POST | `/api/experiments/{id}/cancel` | hentikan eksperimen berjalan |
| GET | `/api/experiments/export?format=csv\|json` | export hasil benchmark |
| GET | `/bench/` | bench site statis deterministik |
| POST | `/api/worker/register` | worker → master (token) |
| POST | `/api/worker/heartbeat` | metrik resource + status |
| POST | `/api/worker/lease` | lease task sesuai kapasitas |
| POST | `/api/worker/tasks/{id}/result` | hasil batch + link baru |
| POST | `/api/worker/tasks/{id}/fail` | requeue / dead-letter |
| WS | `/ws` | event `snapshot`, `node.*`, `job.*`, `task.*`, `worker.failed` |

Detail kontrak: [`docs/API.md`](docs/API.md).

## Membangun panduan HTML (opsional)

Panduan cetak berukuran besar sehingga **tidak di-commit**. Untuk menghasilkan ulang:

```powershell
.\.venv\Scripts\python.exe -m pip install playwright markdown pillow
.\.venv\Scripts\python.exe -m playwright install msedge

# opsional: ambil ulang screenshot dari cluster demo
.\.venv\Scripts\python.exe tools\guides\capture.py

# bangun HTML A4 (diagram Mermaid diunduh otomatis, checksum diverifikasi)
.\.venv\Scripts\python.exe tools\guides\build_html.py
# hasil: docs\CrawlMesh-Panduan-Lengkap.html
```

Buka hasilnya di Edge/Chrome → `Ctrl+P` → **Save as PDF**, A4, **Background graphics ON**.

## Artefak dan repo hygiene

Yang **tidak** masuk repository (lihat `.gitignore`):

| Artefak | Dibuat oleh |
|---|---|
| `master/app/static/` | `cd web && npm run build` |
| `docs/CrawlMesh-Panduan-Lengkap.html` | `tools/guides/build_html.py` |
| `tools/guides/assets/mermaid.min.js` | diunduh otomatis oleh builder (checksum dipatok) |
| `data/`, `*.db*`, `logs/`, `exports/`, `.crawlmesh-agent/` | runtime |
| `.venv/`, `node_modules/`, cache | dependency |

Yang **wajib** di-commit: source Python/TypeScript, `web/package-lock.json`, skrip, test,
dokumen Markdown, gambar `docs/guides/img/*.jpg`, serta konfigurasi contoh `.env.example`.
Line ending dinormalisasi lewat `.gitattributes` (LF untuk kode, CRLF untuk PowerShell).

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Dokumentasi

- [`docs/TDD.md`](docs/TDD.md) — desain teknis, alur, algoritma
- [`docs/architecture.md`](docs/architecture.md) — arsitektur menyeluruh + peta repo
- [`docs/API.md`](docs/API.md) — kontrak REST + WebSocket
- [`docs/RUNBOOK-10NODES.md`](docs/RUNBOOK-10NODES.md) — deployment 10 node
- [`docs/BENCHMARK.md`](docs/BENCHMARK.md) — protokol pengukuran untuk BAB IV
- [`docs/adr/`](docs/adr/) — keputusan arsitektur

## Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | scaffold, kontrak, GUI shell | selesai |
| 1 | cluster discovery, register, heartbeat, role, fault detect | selesai |
| 2 | frontier, decomposition, lease, fetch/parse, aggregation, export | selesai |
| 3 | multiprocessing pool + metrik resource (pool/child process) | selesai (chart menyusul di Phase 6) |
| 4 | dynamic load balancing (static vs dynamic) | selesai |
| 5 | fault tolerance: heartbeat, requeue, retry, dead-letter, simulate failure | selesai |
| 6 | Performance Lab + scalability 1/2/4/6/9 worker + experiment history | selesai |
| 7 | finalisasi, dokumentasi, demo 10 node | berikutnya |

## Troubleshooting

| Gejala | Penyebab | Solusi |
|--------|----------|--------|
| Scan menemukan 0 node | agent tidak jalan / beda token / firewall UDP | cek `/agent/health`, samakan token, izinkan UDP 5599 |
| Agent log `registrasi ditolak` | pairing token salah | salin ulang dari GUI Settings |
| Worker kembali `pending` | belum di-assign | tekan ASSIGN AS WORKER |
| Status berubah `offline` | heartbeat > 15 s | cek koneksi, agent mati, atau port 8000 diblokir |
| GUI 503 | build frontend belum ada | `cd web && npm run build` |
| Port 5599 dipakai proses lain | agent lama masih hidup | hentikan proses python agent sebelumnya |

Catatan Windows: `.venv\Scripts\python.exe` dapat memunculkan proses `python3.13.exe` anak.
Hentikan keduanya saat membersihkan proses agent.

## Lisensi

Proyek akademik — penggunaan internal mata kuliah.
