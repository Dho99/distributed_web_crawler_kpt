# Runbook — Deployment 10 Node

Target UAS: **1 Master + 9 Worker** pada 10 komputer fisik di LAN yang sama.

---

## 1. Isi tabel node sebelum hari-H

| # | Hostname | IP | OS | Cores | RAM | Peran | Port agent |
|---|----------|----|----|-------|-----|-------|-----------|
| 1 |  |  |  |  |  | Master | 8000 |
| 2 |  |  |  |  |  | Worker | 8010 |
| 3 |  |  |  |  |  | Worker | 8010 |
| 4 |  |  |  |  |  | Worker | 8010 |
| 5 |  |  |  |  |  | Worker | 8010 |
| 6 |  |  |  |  |  | Worker | 8010 |
| 7 |  |  |  |  |  | Worker | 8010 |
| 8 |  |  |  |  |  | Worker | 8010 |
| 9 |  |  |  |  |  | Worker | 8010 |
| 10 |  |  |  |  |  | Worker | 8010 |

Catat juga: jenis koneksi (kabel/Wi-Fi), switch/AP, dan apakah jaringan mengisolasi client
(`AP isolation` mematikan komunikasi antar-node — harus dimatikan).

---

## 2. Persiapan jaringan

Master:

```powershell
New-NetFirewallRule -DisplayName "CrawlMesh Master HTTP" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Any
New-NetFirewallRule -DisplayName "CrawlMesh Discovery UDP" -Direction Inbound -Protocol UDP -LocalPort 5599 -Action Allow -Profile Any
```

Worker Windows:

```powershell
New-NetFirewallRule -DisplayName "CrawlMesh Agent HTTP" -Direction Inbound -Protocol TCP -LocalPort 8010 -Action Allow -Profile Any
New-NetFirewallRule -DisplayName "CrawlMesh Discovery UDP" -Direction Inbound -Protocol UDP -LocalPort 5599 -Action Allow -Profile Any
```

Worker Linux:

```bash
sudo ufw allow 8010/tcp
sudo ufw allow 5599/udp
```

Verifikasi dari worker: `Test-NetConnection <master-ip> -Port 8000` (PowerShell) atau
`nc -vz <master-ip> 8000` (Linux).

---

## 3. Instalasi aplikasi

Prasyarat: Python 3.15+ di semua mesin.

Di semua mesin (repo + venv):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

Master juga perlu build GUI (sekali saja, hasil di-commit/di-copy):

```powershell
cd web; npm install; npm run build; cd ..
```

---

## 4. Sinkronisasi token

1. Jalankan Master: `.\scripts\run_master.ps1`.
2. GUI → **Initialize this node as master**.
3. GUI → **Settings** → salin pairing token.
4. Distribusikan token ke worker lewat file `.env` (atau argumen `--token`).

**Jangan** menaruh token di repository publik.

---

## 5. Jalankan agent di 9 worker

Windows (uji manual):

```powershell
.\scripts\run_worker.ps1 -Master http://<MASTER_IP>:8000 -Token <TOKEN> -PoolSize 4
```

Windows (service, jalankan sebagai Administrator):

```powershell
.\scripts\install_agent_windows.ps1 -Master http://<MASTER_IP>:8000 -Token <TOKEN> -PoolSize 4
```

Linux:

```bash
sudo ./scripts/install_agent_linux.sh --master http://<MASTER_IP>:8000 --token <TOKEN> --pool-size 4
```

`PoolSize` disarankan `jumlah core fisik − 1` (maksimum 4–6 agar tidak oversubscribe).

---

## 6. Registrasi cluster lewat GUI

1. Buka `http://<MASTER_IP>:8000`.
2. **Node Discovery** → **SCAN NETWORK** (tunggu ±2.5 s).
3. Untuk node yang muncul: **ASSIGN AS WORKER**.
4. Node yang tidak terdeteksi (beda subnet): isi IP + port di **Add worker by IP**.
5. **Overview** harus menampilkan 9 worker aktif, total core, dan total memory.
6. **Cluster** → klik tiap node untuk memastikan CPU/memory/pool/heartbeat terisi.

---

## 7. Verifikasi acceptance criteria (Phase 1)

| AC | Cara cek | Ekspektasi |
|----|----------|------------|
| AC-01 | inisialisasi master | cluster id + token muncul |
| AC-02 | SCAN NETWORK | agent ditemukan |
| AC-03 | kartu node | role master/worker benar |
| AC-04 | assign 9 worker | semua berstatus active |
| AC-05 | hentikan agent | status → offline ≤ 15 s |
| AC-13 | chart resource | CPU/mem per worker bergerak |

AC-06 s/d AC-12, AC-14 s/d AC-16 diverifikasi setelah Phase 2–6.

---

## 8. Simulasi kegagalan (untuk demo)

Lewat GUI: **Cluster** → pilih worker → **SIMULATE FAILURE**.
Node menjadi `offline` dan tetap offline walau agent hidup, sampai **RECOVER WORKER** ditekan.
Cara realistis: hentikan service agent di mesin tersebut; status berubah otomatis setelah 15 s.

---

## 9. Pengukuran (setelah Phase 6)

- Dataset: bench site di Master (`http://<master>:8000/bench/`), halaman statis.
- Parameter identik untuk semua run: seed, max pages, depth, batch, timeout.
- Ulangi setiap konfigurasi 3× dan ambil median.
- Simpan ekspor CSV dari **Experiment History** sebagai lampiran laporan.

---

## 10. Troubleshooting lapangan

| Gejala | Cek | Tindakan |
|--------|-----|----------|
| Scan 0 node | agent hidup? token sama? UDP 5599? | `http://<worker>:8010/agent/health`, samakan token, buka firewall |
| Worker langsung offline | koneksi ke `:8000` | `Test-NetConnection`, cek switch/VLAN |
| `401 Pairing token tidak valid` | token di argumen agent | salin ulang dari GUI Settings |
| `409 Master belum diinisialisasi` | cluster kosong | tekan Initialize |
| GUI 503 | build frontend hilang | `cd web && npm run build`, restart master |
| Status flicker online/offline | jam/latency | ganti kabel/Wi-Fi, cek interval heartbeat |
| Port 5599 konflik | agent ganda | satu agent per host, atau pilih port berbeda |
| DB terkunci | dua master jalan | pastikan hanya satu proses master |

---

## 11. Checklist hari-H

- [ ] Tabel node terisi (hostname/IP/OS)
- [ ] Firewall 8000/TCP, 8010/TCP, 5599/UDP terbuka
- [ ] Master diinisialisasi, token dibagikan
- [ ] 9 agent berjalan (service/manual)
- [ ] 9 worker di-assign dan `active`
- [ ] Simulasi kegagalan + recovery diuji
- [ ] Export hasil/eksperimen siap
- [ ] Rekaman demo ≤ 5 menit disiapkan
