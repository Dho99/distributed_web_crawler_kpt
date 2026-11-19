# CrawlMesh API Contract (v0.1)

Base URL: `http://<master>:8000`. GUI memakai origin yang sama; agent memakai header
`X-Cluster-Token` pada semua endpoint `/api/worker/*`.

Status: seluruh endpoint di bawah aktif. Benchmark otomatis (Phase 6) belum ada.

---

## System

### `GET /api/health`

```json
{ "status": "ok", "service": "crawlmesh-master", "version": "0.1.0",
  "cluster_id": "CM-60CB65", "initialized": true, "db": "data/crawlmesh.db" }
```

---

## Cluster

### `POST /api/cluster/init`

Body opsional: `{ "name": "CrawlMesh Lab", "master_url": "http://192.168.18.141:8000" }`

Idempoten: jika cluster sudah ada, mengembalikan cluster yang sama.

```json
{ "cluster_id": "CM-60CB65", "name": "CrawlMesh Lab",
  "pairing_token": "dYTS…Lml1", "master_url": "http://192.168.18.141:8000",
  "discovery_port": 5599, "created_at": "2026-11-19T13:51:24Z" }
```

### `GET /api/cluster`

`ClusterInfo | null`.

### `GET /api/cluster/overview`

```json
{ "cluster": { … }, "total_nodes": 2, "active_workers": 1, "offline_workers": 0,
  "total_cpu_cores": 32, "total_memory": 42288463872, "running_jobs": 0,
  "pages_crawled": 0, "failed_tasks": 0, "current_throughput": 0.0,
  "nodes": [ { "worker_id": "worker-…", "role": "worker", "status": "idle", … } ] }
```

`current_throughput` = jumlah hasil 10 detik terakhir / 10.

### `POST /api/cluster/discover`

Menunggu ±2.5 s (probe 2× broadcast + loopback).

```json
{ "found": [ { "worker_id": "worker-…", "hostname": "LAB-PC-2",
               "ip_address": "192.168.18.142", "port": 8010, "cpu_cores": 8,
               "memory_total": 17179869184, "os_name": "Windows 11",
               "cluster_id": "CM-60CB65", "already_known": false } ],
  "scanned_ms": 2500, "already_known": [] }
```

---

## Nodes

| Method | Path | Body | Efek |
|--------|------|------|------|
| GET | `/api/nodes` | — | daftar node (status `removed` disembunyikan) |
| GET | `/api/nodes/{worker_id}` | — | detail, 404 bila tidak ada |
| POST | `/api/nodes/{worker_id}/assign` | — | `pending/offline → online`, worker mulai menerima task |
| POST | `/api/nodes/{worker_id}/remove` | — | status `removed`, lease dihentikan |
| POST | `/api/nodes/{worker_id}/simulate-failure` | — | status `offline`, `simulated_offline=1` (heartbeat tidak memulihkan) |
| POST | `/api/nodes/{worker_id}/recover` | — | `simulated_offline=0`, status `online` |
| POST | `/api/nodes/manual` | `{ "ip_address": "192.168.18.142", "port": 8010 }` | probe `/agent/info`, simpan sebagai `pending` |

Contoh node:

```json
{ "worker_id": "worker-fcm-loq-259b78", "hostname": "FCM-LOQ", "ip_address": "192.168.18.141",
  "port": 8010, "role": "worker", "status": "idle", "cpu_cores": 16, "memory_total": 21144231936,
  "os_name": "Windows 11", "python_version": "3.13.14", "pool_size": 2, "capacity": 2,
  "cpu_usage": 13.7, "memory_usage": 72.1, "inflight": 0, "child_processes": 0,
  "throughput": 0.0, "last_heartbeat": "2026-11-19T13:58:27Z" }
```

---

## Worker → Master

Semua endpoint memerlukan `X-Cluster-Token`. Token salah → `401`; cluster belum init → `409`.

### `POST /api/worker/register`

```json
{ "worker_id": "worker-fcm-loq-259b78", "hostname": "FCM-LOQ", "ip_address": "192.168.18.141",
  "port": 8010, "cpu_cores": 16, "memory_total": 21144231936, "os_name": "Windows 11",
  "python_version": "3.13.14", "agent_version": "0.1.0", "pool_size": 4, "capacity": 4 }
```

Balasan:

```json
{ "worker_id": "worker-fcm-loq-259b78", "cluster_id": "CM-60CB65", "status": "pending",
  "accepted": true, "heartbeat_interval": 5, "offline_threshold": 15, "message": "…" }
```

`worker_id` boleh kosong → master membuat id. Registrasi ulang mempertahankan status assignment.

### `POST /api/worker/heartbeat`

```json
{ "worker_id": "worker-…",
  "metrics": { "cpu_usage": 12.5, "memory_usage": 40.2, "child_processes": 4,
               "active_tasks": 2, "inflight": 2, "capacity": 4, "throughput": 1.8 },
  "status": "busy", "current_job_ids": ["job-…"] }
```

```json
{ "acknowledged": true, "assigned": true, "status": "busy",
  "control": { "pause_all": false, "paused_job_ids": [], "server_time": "…" } }
```

`assigned=false` → agent berhenti melakukan lease. Status `offline` karena simulasi juga
mengembalikan `assigned=false` sampai operator menekan RECOVER.

### `POST /api/worker/lease`

```json
{ "worker_id": "worker-…", "free_slots": 2 }
```

```json
{ "tasks": [ { "task_id": "task-…", "job_id": "job-…",
               "urls": ["https://…"], "depth": 1, "attempt": 1,
               "request_timeout": 15.0, "domain_delay": 0.5, "respect_robots": true,
               "allow_private_targets": false, "max_links_per_page": 50 } ],
  "control": { … } }
```

Master mereservasi kapasitas (`inflight += len(tasks)`) saat lease diberikan. Dynamic mode tidak
memberi lease jika `cpu_usage > 92`; static mode hanya mengembalikan task yang sudah
dipre-assign ke worker tersebut.

### `POST /api/worker/tasks/{task_id}/result`

```json
{ "worker_id": "worker-…",
  "results": [ { "url": "https://…", "final_url": "https://…", "http_status": 200,
                 "title": "…", "extracted_text": "…", "links": ["https://…"],
                 "content_hash": "…", "response_time_ms": 142.3, "size_bytes": 20480,
                 "content_type": "text/html", "error": null } ],
  "links": [],
  "processing_ms": 210.4 }
```

Balasan:

```json
{ "accepted": 4, "duplicates": 0, "failed": 1, "links_accepted": 31, "job_completed": false }
```

Hasil ditulis dengan `ON CONFLICT (job_id, url_hash) DO NOTHING`, jadi retry tidak menggandakan
data. Link dari halaman dimasukkan ke frontier dengan depth `task.depth + 1`.

### `POST /api/worker/tasks/{task_id}/fail`

`{ "worker_id": "…", "error": "timeout", "retriable": true }`

Requeue bila `attempt < max_attempts`, dead-letter bila sudah mencapai batas. Worker yang mati
tanpa mengirim result akan di-requeue oleh detektor heartbeat.

---

## Crawl jobs

| Method | Path | Keterangan |
|--------|------|------------|
| POST | `/api/jobs` | body `CrawlJobConfig`; job langsung `running` |
| GET | `/api/jobs` | daftar + statistik agregat |
| GET | `/api/jobs/{id}` | detail + progres |
| POST | `/api/jobs/{id}/pause` | hentikan leasing job |
| POST | `/api/jobs/{id}/resume` | lanjutkan job paused |
| POST | `/api/jobs/{id}/cancel` | batalkan task/frontier aktif |
| GET | `/api/jobs/{id}/frontier` | `{ "finished": 41, "queued": 0 }` |
| GET | `/api/tasks?job_id&status&worker&limit` | ledger task |
| GET | `/api/results?job_id&q&status&worker&limit&offset` | `{ total, items }` |
| GET | `/api/results/export?format=csv\|json&job_id` | unduh hasil |
| GET | `/api/metrics/timeseries?minutes=10` | sampel resource worker |

Contoh create:

```json
{ "job_name": "Bench Crawl", "seed_urls": ["http://192.168.18.141:8000/bench/"],
  "maximum_pages": 150, "maximum_depth": 2, "batch_size": 5,
  "request_timeout": 10, "domain_delay": 0.05,
  "respect_robots": true, "scheduling_mode": "dynamic" }
```

Seed pada host Master dengan path `/bench` otomatis mengaktifkan `allow_private_targets` (bench
site); seed privat lain ditolak dengan `400`.

---

## Experiments

| Method | Path | Keterangan |
|--------|------|------------|
| POST | `/api/experiments/run` | runner benchmark; 409 jika sudah ada run aktif |
| GET | `/api/experiments?limit&group_id` | riwayat, `group_id` untuk isi satu suite |
| GET | `/api/experiments/busy` | `{ "running": bool }` |
| GET | `/api/experiments/{id}?samples=true` | detail + trace resource |
| POST | `/api/experiments/{id}/cancel` | batalkan run (job ikut dibatalkan) |
| GET | `/api/experiments/export?format=csv\|json` | unduh riwayat |

Body `POST /api/experiments/run`:

```json
{ "experiment_type": "distributed", "worker_count": 4,
  "maximum_pages": 120, "maximum_depth": 2, "batch_size": 5,
  "domain_delay": 0.0, "scheduling_mode": "dynamic", "repeat": 3 }
```

`experiment_type`: `sequential | local_parallel | distributed | scalability`.
Mode `load_balancing` dan `fault_tolerance` dijalankan lewat Crawl Jobs + simulasi failure
(bukan runner benchmark) dan akan ditolak dengan `400`.

Setiap run diulang `repeat` kali (1–7, default 3) dan diambil median execution time.

Response:

```json
{ "experiment_id": "exp-ab12cd34", "experiment_type": "distributed", "status": "pending",
  "worker_count": 4, "group_id": "exp-ab12cd34", "total_pages": 120, "progress_pages": 0, … }
```

Metrik akhir:

```json
{ "status": "completed", "execution_time_ms": 4395.4, "pages_ok": 120, "pages_failed": 0,
  "speedup": 1.84, "efficiency": 46.0, "throughput": 27.3,
  "cpu_utilization": 62.4, "memory_utilization": 71.2,
  "baseline_id": "exp-9911aa02", "workload_key": "6b3f…" }
```

---

## Bench site

`GET /bench/` menampilkan index 40 link, `GET /bench/{n}.html` (1–300) menyajikan halaman statis
deterministik ±120 KB dengan 32 link acak deterministik. `GET /robots.txt` dan
`/bench/robots.txt` mengizinkan semua crawler. `GET /bench/_warm` merender semua halaman lebih
awal sehingga pengukuran benchmark tidak menghitung biaya generasi konten.

---

## WebSocket `/ws`

Server mengirim snapshot saat connect, lalu event:

| `kind` | payload | kapan |
|--------|---------|-------|
| `snapshot` | `Overview` | saat koneksi dibuka |
| `cluster.initialized` | `ClusterInfo` | master diinisialisasi |
| `node.updated` | `NodeInfo` | registrasi / heartbeat / assign |
| `node.offline` | `{ worker_id, detected_at }` | heartbeat melewati threshold |
| `node.removed` | `{ worker_id }` | node dihapus operator |
| `failure.simulated` | `{ worker_id }` | tombol SIMULATE FAILURE |
| `pong` | `{ clients }` | balasan pesan `ping` |

Format: `{ "kind": "...", "ts": "<ISO-8601>", "payload": { … } }`.

---

## Error format

```json
{ "detail": "Pesan error yang dapat dibaca operator" }
```

| Code | Arti |
|------|------|
| 401 | pairing token salah / tidak dikirim |
| 404 | node/task tidak ditemukan |
| 409 | master belum diinisialisasi |
| 502 | agent tidak dapat dihubungi saat add-by-IP |
