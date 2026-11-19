
PRD berikut disusun dengan mengacu pada dokumen UAS yang Anda lampirkan dan hanya menggunakan konteks percakapan ini.

Saya mengambil **Tema Nomor 8 — Distributed Web Crawler**. Ada satu hal penting dalam perancangannya: aplikasi tidak cukup hanya memiliki GUI untuk menjalankan crawling. GUI harus menjadi pusat kendali arsitektur Master–Worker, termasuk penemuan node, identifikasi peran, distribusi pekerjaan, pemantauan, dan evaluasi performa.

Berdasarkan ketentuan UAS, sistem harus mendukung minimal 10 node fisik (1 Master + 9 Worker), multiprocessing pada setiap Worker, komunikasi terdistribusi, dynamic load balancing, dan fault tolerance. Pengujiannya juga harus mencakup sequential, local parallel, distributed, serta scalability dengan 1, 2, 4, 6, dan 9 Worker.&#x20;

UJIAN AKHIR SEMESTER.pdf

Berikut PRD lengkapnya.

# PRODUCT REQUIREMENTS DOCUMENT (PRD)

# CRAWLMESH

## Distributed Web Crawler with Graphical Master–Worker Orchestration

**Versi Dokumen:** 1.0
**Status:** Proposed
**Kategori:** Distributed Computing / Parallel Processing
**Mata Kuliah:** Komputasi Paralel dan Sistem Terdistribusi
**Arsitektur:** Master–Worker
**Jumlah Node Target:** 10 Node (1 Master + 9 Worker)
**Platform:** Web-based GUI
**Jenis Aplikasi:** Distributed Web Crawling and Monitoring System

---

# 1. EXECUTIVE SUMMARY

## 1.1 Product Overview

CrawlMesh merupakan aplikasi Distributed Web Crawler yang dirancang untuk mengambil, mengumpulkan, dan memproses informasi dari sejumlah halaman web dengan memanfaatkan arsitektur komputasi paralel dan sistem terdistribusi berbasis Master–Worker.

Sistem membagi pekerjaan crawling menjadi sejumlah task independen yang kemudian didistribusikan oleh Master kepada beberapa Worker melalui jaringan komputer.

Setiap Worker memiliki kemampuan multiprocessing sehingga dapat memanfaatkan beberapa core CPU secara bersamaan dalam menjalankan pekerjaan crawling dan pemrosesan konten halaman web.

Berbeda dengan implementasi distributed crawler konvensional yang mengharuskan pengguna melakukan konfigurasi node melalui terminal atau command line, CrawlMesh menyediakan antarmuka GUI sebagai pusat pengelolaan cluster.

Melalui GUI tersebut, pengguna dapat:

1. Mendeteksi node yang tersedia dalam jaringan.
2. Mengidentifikasi node yang berperan sebagai Master dan Worker.
3. Mendaftarkan Worker ke dalam cluster.
4. Memantau status dan kemampuan setiap Worker.
5. Membuat pekerjaan crawling.
6. Mengatur distribusi pekerjaan secara otomatis.
7. Memantau proses crawling secara real-time.
8. Melakukan simulasi kegagalan Worker.
9. Mengukur performa sistem komputasi paralel dan terdistribusi.
10. Mengekspor hasil crawling dan laporan pengujian.

Tujuan utama CrawlMesh adalah memberikan demonstrasi nyata bahwa proses web crawling dapat diselesaikan melalui kolaborasi sejumlah komputer yang bekerja secara paralel dan terdistribusi.

## 1.2 Problem Statement

Implementasi distributed web crawler memiliki beberapa tantangan:

- Identifikasi dan konfigurasi Master serta Worker membutuhkan pemahaman teknis jaringan.
- Pembagian pekerjaan kepada banyak Worker membutuhkan mekanisme koordinasi.
- Perbedaan kemampuan hardware menyebabkan distribusi beban yang tidak selalu merata.
- Worker dapat mengalami kegagalan koneksi atau berhenti beroperasi ketika proses crawling berlangsung.
- Pengguna kesulitan mengetahui kondisi cluster dan progres crawling apabila tidak tersedia sistem monitoring terpusat.
- Pengukuran performa komputasi paralel dan terdistribusi membutuhkan pencatatan metrik yang sistematis.

CrawlMesh dirancang untuk menyelesaikan permasalahan tersebut melalui orkestrasi cluster berbasis GUI dan mekanisme distributed processing otomatis.

## 1.3 Product Vision

Membangun aplikasi web crawler terdistribusi yang memungkinkan pengguna mengelola banyak komputer sebagai satu kesatuan sistem komputasi melalui antarmuka grafis yang sederhana, terukur, dan mudah dipahami.

---

# 2. PROJECT OBJECTIVES

## 2.1 Primary Objectives

1. Mengimplementasikan distributed web crawler menggunakan arsitektur Master–Worker.
2. Mengimplementasikan pembagian pekerjaan crawling menjadi task independen.
3. Mengimplementasikan multiprocessing pada masing-masing Worker untuk memanfaatkan multicore CPU.
4. Mengimplementasikan komunikasi jaringan antara Master dan Worker.
5. Mengimplementasikan dynamic load balancing berdasarkan kondisi Worker.
6. Mengimplementasikan fault tolerance untuk menangani kegagalan Worker.
7. Menyediakan GUI untuk mempermudah identifikasi, konfigurasi, dan monitoring node.
8. Menyediakan fasilitas pengukuran performa sistem secara otomatis.

## 2.2 Success Criteria

Sistem dinyatakan berhasil apabila:

| ID    | Kriteria               | Target                                             |
| ----- | ---------------------- | -------------------------------------------------- |
| SC-01 | Master node            | 1 node aktif                                       |
| SC-02 | Worker node            | 9 node fisik terdaftar                             |
| SC-03 | Node discovery         | Worker dapat ditemukan melalui GUI                 |
| SC-04 | Multiprocessing        | Setiap Worker menjalankan beberapa proses          |
| SC-05 | Task distribution      | Task dapat didistribusikan ke beberapa Worker      |
| SC-06 | Load balancing         | Distribusi pekerjaan menyesuaikan kondisi Worker   |
| SC-07 | Fault tolerance        | Task gagal dapat di-requeue dan diproses ulang     |
| SC-08 | Monitoring             | Status dan penggunaan resource dapat dipantau      |
| SC-09 | Performance evaluation | Seluruh metrik evaluasi dapat dihasilkan           |
| SC-10 | Scalability            | Pengujian 1, 2, 4, 6, dan 9 Worker dapat dilakukan |

---

# 3. TARGET USERS

## 3.1 Primary User: System Operator

Pengguna yang bertanggung jawab mengoperasikan sistem distributed crawler.

Kebutuhan:

- Mengetahui node yang tersedia.
- Menentukan Master dan Worker.
- Menjalankan crawling tanpa konfigurasi command line berulang.
- Memantau distribusi pekerjaan.
- Mengetahui kondisi setiap Worker.

## 3.2 Secondary User: System Administrator

Pengguna yang bertanggung jawab atas konfigurasi dan kesehatan sistem.

Kebutuhan:

- Mengelola koneksi jaringan.
- Mengatur jumlah multiprocessing setiap Worker.
- Memantau CPU dan memory.
- Mengaktifkan atau menonaktifkan Worker.
- Mengidentifikasi Worker yang mengalami kegagalan.

## 3.3 Evaluator / Lecturer

Pengguna yang membutuhkan bukti bahwa implementasi komputasi paralel dan terdistribusi berjalan sesuai ketentuan.

Kebutuhan:

- Melihat arsitektur Master–Worker.
- Memverifikasi jumlah Worker aktif.
- Mengamati distribusi task.
- Melihat simulasi fault tolerance.
- Membandingkan hasil pengujian sequential, local parallel, dan distributed.
- Melihat metrik speedup, efficiency, throughput, dan resource utilization.

---

# 4. PRODUCT SCOPE

## 4.1 In Scope

Fitur yang wajib dikembangkan:

1. Cluster management.
2. Master–Worker discovery.
3. Node registration dan role identification.
4. Worker health monitoring.
5. Crawl job management.
6. URL frontier management.
7. Task decomposition.
8. Distributed task scheduling.
9. Worker multiprocessing.
10. Dynamic load balancing.
11. Fault tolerance dan task recovery.
12. Crawl result aggregation.
13. Performance monitoring.
14. Experiment management.
15. Data export.

## 4.2 Out of Scope

Fitur berikut tidak menjadi prioritas pengembangan:

- Search engine publik seperti Google.
- Web scraping yang memerlukan autentikasi akun pihak ketiga.
- Bypass CAPTCHA atau mekanisme proteksi website.
- Browser automation untuk halaman yang membutuhkan interaksi kompleks.
- Distributed storage berskala besar.
- Multi-master high availability.
- Automatic cloud infrastructure provisioning.
- Sistem crawling tanpa batas terhadap seluruh internet.

Fokus utama adalah membuktikan mekanisme komputasi paralel dan sistem terdistribusi.

---

# 5. SYSTEM ARCHITECTURE

## 5.1 Architectural Overview

CrawlMesh menggunakan arsitektur Master–Worker dengan satu Master sebagai pusat koordinasi dan sembilan Worker sebagai pelaksana pekerjaan crawling.

### Master Node

Master bertanggung jawab untuk:

- Mengelola cluster.
- Mendeteksi dan mendaftarkan Worker.
- Menyimpan URL frontier.
- Memecah pekerjaan menjadi task.
- Mendistribusikan task kepada Worker.
- Mengatur dynamic load balancing.
- Menerima hasil crawling.
- Mengelola retry dan requeue.
- Mengumpulkan metrik performa.
- Menyediakan dashboard GUI.

### Worker Node

Worker bertanggung jawab untuk:

- Melakukan registrasi kepada Master.
- Mengirim heartbeat.
- Menerima task crawling.
- Melakukan HTTP request.
- Mengunduh konten halaman web.
- Melakukan parsing dan ekstraksi informasi.
- Menggunakan multiprocessing untuk pemrosesan paralel.
- Mengirim hasil kepada Master.
- Melaporkan kondisi CPU dan memory.

## 5.2 Logical Architecture

```
                  USER
                    |
                    v
          +---------------------+
          |     WEB GUI         |
          | Cluster Dashboard   |
          | Crawler Management  |
          | Performance Monitor |
          +----------+----------+
                     |
                     v
          +---------------------+
          |     MASTER NODE     |
          |---------------------|
          | Node Manager        |
          | Task Scheduler      |
          | URL Frontier        |
          | Load Balancer       |
          | Fault Tolerance     |
          | Result Aggregator   |
          | Metrics Collector   |
          +----------+----------+
                     |
              Network / LAN
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
   +--------+    +--------+    +--------+
   |Worker 1|    |Worker 2|    |Worker 3|
   |--------|    |--------|    |--------|
   | Agent  |    | Agent  |    | Agent  |
   |Process |    |Process |    |Process |
   | Pool   |    | Pool   |    | Pool   |
   +--------+    +--------+    +--------+
       |             |             |
       +-------------+-------------+
                     |
              ... Worker 9
                     |
                     v
              CRAWL RESULTS
                     |
                     v
              MASTER AGGREGATOR
                     |
                     v
                DATABASE
```

## 5.3 Node Configuration

| Komponen | Jumlah | Fungsi                            |
| -------- | ------ | --------------------------------- |
| Master   | 1      | Koordinasi dan pengelolaan sistem |
| Worker   | 9      | Pemrosesan crawling               |
| Total    | 10     | Infrastruktur distributed system  |

Setiap Worker wajib memiliki:

- Worker Agent.
- Network connectivity.
- Multiprocessing capability.
- HTTP crawling module.
- HTML parsing module.
- Resource monitoring module.

## 5.4 Communication Mechanism

Komunikasi Master dan Worker menggunakan protokol jaringan berbasis HTTP atau WebSocket.

Jenis komunikasi:

| Komunikasi      | Arah             | Fungsi                  |
| --------------- | ---------------- | ----------------------- |
| Registration    | Worker → Master | Mendaftarkan Worker     |
| Heartbeat       | Worker → Master | Melaporkan status       |
| Task dispatch   | Master → Worker | Mengirim pekerjaan      |
| Task result     | Worker → Master | Mengirim hasil crawling |
| Resource report | Worker → Master | Mengirim CPU dan memory |
| Task recovery   | Master → Worker | Mengirim ulang task     |

Setiap Worker memiliki identitas unik berupa Worker ID.

---

# 6. CORE FEATURE REQUIREMENTS

# 6.1 Cluster Discovery & Role Identification

**Priority: P0 — Critical**

Fitur ini merupakan salah satu pembeda utama CrawlMesh.

Pengguna tidak perlu melakukan identifikasi node satu per satu melalui terminal. Sistem menyediakan GUI untuk menemukan node yang tersedia dan mengelola perannya.

### 6.1.1 Master Initialization

Ketika aplikasi pertama kali dijalankan, pengguna dapat memilih:

**Initialize This Node as Master**

Setelah dikonfirmasi, sistem:

1. Menginisialisasi layanan Master.
2. Membuat Cluster ID.
3. Mengaktifkan Node Manager.
4. Menyediakan endpoint komunikasi.
5. Menghasilkan pairing token untuk Worker.
6. Menampilkan dashboard cluster.

Hanya satu Master aktif yang diperbolehkan dalam satu cluster.

### 6.1.2 Automatic Worker Discovery

Master menyediakan tombol:

**[ DISCOVER WORKERS ]**

Ketika tombol diklik, sistem akan:

1. Memindai keberadaan Worker Agent pada jaringan lokal.
2. Menerima informasi node yang ditemukan.
3. Memverifikasi identitas dan kemampuan Worker.
4. Mengambil informasi hardware.
5. Menampilkan daftar Worker yang tersedia.
6. Mengidentifikasi status koneksi masing-masing node.

Informasi yang ditampilkan:

| Informasi         | Keterangan                |
| ----------------- | ------------------------- |
| Worker ID         | Identitas node            |
| Hostname          | Nama komputer             |
| IP Address        | Alamat jaringan           |
| CPU Cores         | Jumlah core CPU           |
| RAM               | Kapasitas memory          |
| Agent Status      | Status Worker Agent       |
| Node Role         | Master / Worker           |
| Connection Status | Online / Offline          |
| Process Capacity  | Kemampuan multiprocessing |

### 6.1.3 Role Assignment

Setelah node ditemukan, pengguna dapat memilih node dan menekan:

**[ ASSIGN AS WORKER ]**

Sistem akan:

1. Memvalidasi kemampuan node.
2. Mendaftarkan node ke cluster.
3. Menentukan Worker ID.
4. Mengaktifkan komunikasi dengan Master.
5. Memulai heartbeat.
6. Menampilkan node sebagai Worker aktif.

Untuk Master, pengguna menggunakan tindakan:

**[ SET AS MASTER ]**

Role ditentukan secara eksplisit dan diverifikasi melalui registrasi. Sistem tidak boleh mengasumsikan sebuah komputer sebagai Master hanya berdasarkan IP Address.

### 6.1.4 Discovery Fallback

Penemuan otomatis melalui broadcast atau mDNS dapat dibatasi oleh konfigurasi jaringan.

Oleh karena itu, GUI juga harus menyediakan:

- Add Worker by IP Address.
- Connect Using Pairing Token.
- Refresh Node Discovery.

Dengan demikian, pengguna tetap dapat menghubungkan Worker meskipun berada pada subnet berbeda.

**Catatan implementasi:** Fitur klik untuk discovery mengasumsikan Worker Agent sudah terpasang dan berjalan pada masing-masing komputer. Instalasi awal agent merupakan prasyarat infrastruktur; setelah itu, penemuan dan pengelolaan node dilakukan melalui GUI tanpa konfigurasi CLI berulang.

---

# 6.2 Cluster Dashboard

**Priority: P0 — Critical**

Dashboard merupakan halaman utama setelah Master aktif.

Informasi utama:

### Cluster Overview

- Total Nodes.
- Active Workers.
- Offline Workers.
- Total CPU Cores.
- Total Memory.
- Current Running Jobs.
- Completed Tasks.
- Failed Tasks.

### Node Status Visualization

Setiap node ditampilkan sebagai kartu.

Contoh:

| Node      | Role   | CPU | Memory | Status  |
| --------- | ------ | --- | ------ | ------- |
| Master-01 | Master | 25% | 40%    | Online  |
| Worker-01 | Worker | 35% | 55%    | Online  |
| Worker-02 | Worker | 70% | 65%    | Online  |
| Worker-03 | Worker | 0%  | 0%     | Offline |
| Worker-04 | Worker | 42% | 50%    | Online  |

Status node menggunakan indikator:

- Online.
- Busy.
- Idle.
- Degraded.
- Offline.

Dashboard harus diperbarui secara berkala tanpa mengharuskan pengguna melakukan refresh manual.

---

# 6.3 Crawl Job Management

**Priority: P0 — Critical**

Pengguna dapat membuat pekerjaan crawling melalui GUI.

### Create Crawl Job

Pengguna memasukkan konfigurasi berikut:

| Parameter          | Deskripsi                  |
| ------------------ | -------------------------- |
| Job Name           | Nama pekerjaan             |
| Seed URL           | URL awal crawling          |
| Allowed Domains    | Domain yang diperbolehkan  |
| Maximum Pages      | Jumlah maksimum halaman    |
| Maximum Depth      | Kedalaman crawling         |
| Batch Size         | Jumlah URL per task        |
| Request Timeout    | Batas waktu HTTP request   |
| Domain Delay       | Jeda permintaan per domain |
| Respect Robots.txt | Menghormati robots.txt     |
| User Agent         | Identitas crawler          |

Contoh konfigurasi:

```
Job Name       : Research Crawler
Seed URL       : https://example.com
Maximum Pages  : 1000
Maximum Depth  : 3
Batch Size     : 10
Timeout        : 15 seconds
Workers        : Automatic
Robots.txt     : Enabled
```

Setelah konfigurasi selesai, pengguna menekan:

**[ START CRAWLING ]**

Sistem kemudian membuat Crawl Job dan memasukkannya ke Task Scheduler.

### Job Status

- Pending.
- Running.
- Paused.
- Completed.
- Failed.
- Cancelled.

---

# 6.4 Task Decomposition

**Priority: P0 — Critical**

Sistem harus mampu membagi pekerjaan crawling menjadi task independen.

Proses:

1. Master menerima Seed URL.
2. Master memasukkan URL ke URL Frontier.
3. URL dinormalisasi.
4. Sistem melakukan deduplication.
5. URL dikelompokkan menjadi task berukuran kecil.
6. Task dimasukkan ke task queue.
7. Task dikirim kepada Worker yang tersedia.

Setiap task minimal memiliki:

- Task ID.
- Crawl Job ID.
- URL List.
- Crawl Depth.
- Priority.
- Assigned Worker.
- Attempt Count.
- Task Status.
- Created Timestamp.

Task harus memiliki identitas unik untuk mencegah duplikasi pemrosesan.

Setelah Worker menemukan URL baru dari halaman yang berhasil diproses, hasil link dikirim kepada Master untuk dimasukkan kembali ke URL Frontier jika memenuhi aturan crawling.

Dengan demikian, crawling dapat berlangsung secara bertahap hingga batas halaman atau kedalaman tercapai.

---

# 6.5 Worker Multiprocessing

**Priority: P0 — Critical**

Setiap Worker wajib menggunakan multiprocessing untuk memanfaatkan multicore CPU.

Mekanisme:

1. Worker menerima sekumpulan URL.
2. Worker melakukan HTTP request.
3. Konten HTML diterima.
4. Konten diberikan kepada multiprocessing pool.
5. Setiap process melakukan pemrosesan konten secara independen.
6. Hasil setiap process dikembalikan kepada Worker Agent.
7. Worker mengirim hasil kepada Master.

Aktivitas yang dapat diproses secara paralel:

- HTML parsing.
- Title extraction.
- Text extraction.
- Link extraction.
- URL normalization.
- Content hashing.
- Metadata extraction.

Jumlah process dapat dikonfigurasi berdasarkan kemampuan CPU.

Contoh:

```
Worker-01
CPU Cores       : 8
Multiprocessing : 4 Processes
Active Tasks    : 4
```

Penggunaan multiprocessing harus dapat dibuktikan melalui pemantauan resource dan jumlah proses pada masing-masing Worker.

Catatan: HTTP fetching dapat menggunakan concurrency I/O, sedangkan parsing dan ekstraksi konten menjadi pekerjaan CPU-parallel melalui multiprocessing. Keduanya harus dikelola agar tidak menghasilkan jumlah proses yang berlebihan.

---

# 6.6 Dynamic Load Balancing

**Priority: P0 — Critical**

Master harus mampu mendistribusikan task secara dinamis berdasarkan kondisi aktual Worker.

Sistem tidak boleh hanya membagikan pekerjaan dengan jumlah yang sama tanpa mempertimbangkan kemampuan node.

### Worker Metrics

Master mengumpulkan:

- CPU Utilization.
- Memory Utilization.
- Active Processes.
- Active Tasks.
- Pending Tasks.
- Average Processing Time.
- Completed Tasks.
- Worker Health.

### Scheduling Strategy

Menggunakan pendekatan Weighted Least Loaded Scheduling.

Contoh:

| Worker | CPU | Memory | Active Tasks | Kondisi    |
| ------ | --- | ------ | ------------ | ---------- |
| W1     | 20% | 30%    | 1            | Available  |
| W2     | 85% | 80%    | 8            | Overloaded |
| W3     | 35% | 40%    | 2            | Available  |
| W4     | 50% | 45%    | 3            | Normal     |

Master akan lebih memprioritaskan Worker yang memiliki kapasitas pemrosesan lebih tersedia.

Faktor penilaian:

- CPU utilization.
- Memory availability.
- Active task count.
- Processing throughput.
- Worker health.

### Expected Behavior

Ketika W2 mengalami peningkatan beban, Master akan mengurangi alokasi task baru kepadanya dan mendistribusikan pekerjaan berikutnya kepada Worker yang lebih tersedia.

Distribusi beban harus diperbarui secara berkala berdasarkan laporan resource terbaru.

Sistem juga harus menyediakan dua mode eksperimen:

1. Static Scheduling.
2. Dynamic Load Balancing.

Keduanya digunakan untuk membandingkan distribusi pekerjaan dan performa sistem.

---

# 6.7 Fault Tolerance

**Priority: P0 — Critical**

Sistem harus mampu menangani kegagalan Worker ketika crawling sedang berlangsung.

### Worker Heartbeat

Setiap Worker mengirim heartbeat secara periodik kepada Master.

Default konfigurasi:

- Heartbeat interval: 5 detik.
- Offline threshold: 15 detik.
- Task retry limit: 3 kali.

Konfigurasi dapat disesuaikan.

### Failure Detection

Ketika Worker tidak mengirim heartbeat dalam batas waktu yang ditentukan:

1. Master mendeteksi Worker tidak responsif.
2. Status Worker berubah menjadi Offline.
3. Task yang belum selesai diidentifikasi.
4. Task yang belum memiliki hasil valid dikembalikan ke queue.
5. Task didistribusikan kepada Worker lain.
6. Master mencatat waktu pemulihan.

### Retry Mechanism

Setiap task memiliki Attempt Count.

Contoh:

```
Task ID: TASK-001

Attempt 1:
Worker-02 -> Failed

Attempt 2:
Worker-04 -> Success

Final Status:
Completed
```

Jika batas retry terlampaui, task dipindahkan ke Failed Task Queue untuk ditinjau.

### Failure Simulation

GUI menyediakan fitur:

**[ SIMULATE WORKER FAILURE ]**

Fitur ini digunakan untuk pengujian akademik.

Pengguna dapat memilih Worker tertentu untuk disimulasikan mengalami kegagalan. Selain itu, pengujian dapat dilakukan dengan menghentikan Worker Agent atau memutus koneksi jaringan secara langsung.

Dashboard harus memperlihatkan:

- Worker yang mengalami kegagalan.
- Waktu deteksi kegagalan.
- Jumlah task terdampak.
- Jumlah task yang di-requeue.
- Worker pengganti.
- Recovery Time.

---

# 6.8 Result Aggregation

**Priority: P0 — Critical**

Master bertugas mengumpulkan dan menggabungkan hasil dari seluruh Worker.

Informasi hasil crawling:

| Field          | Deskripsi             |
| -------------- | --------------------- |
| URL            | Alamat halaman        |
| HTTP Status    | Status HTTP           |
| Page Title     | Judul halaman         |
| Extracted Text | Konten teks           |
| Links Found    | Jumlah link ditemukan |
| Content Hash   | Identitas konten      |
| Response Time  | Waktu request         |
| Worker ID      | Worker pemroses       |
| Crawled At     | Waktu crawling        |

Master harus memastikan bahwa hasil yang sama tidak disimpan berulang kali akibat mekanisme retry.

Hasil crawling disimpan secara terpusat sehingga dapat diakses melalui GUI.

---

# 6.9 Performance Monitoring

**Priority: P0 — Critical**

Sistem harus menyediakan monitoring performa secara real-time.

Informasi:

- Total Pages Crawled.
- Pending URLs.
- Completed Tasks.
- Failed Tasks.
- Pages per Second.
- Average Response Time.
- CPU Utilization per Worker.
- Memory Utilization per Worker.
- Worker Throughput.

Visualisasi yang disediakan:

1. Crawling Progress Chart.
2. Worker CPU Utilization Chart.
3. Worker Memory Utilization Chart.
4. Task Distribution Chart.
5. Throughput Timeline.
6. Worker Health Timeline.

---

# 6.10 Experiment & Benchmarking Module

**Priority: P0 — Critical**

Fitur ini dirancang khusus untuk mendukung pengujian dan evaluasi sesuai ketentuan UAS.

Pengguna dapat menjalankan eksperimen melalui GUI tanpa harus mengubah konfigurasi program secara manual.

### Experiment Modes

**A. Sequential Processing**

Menjalankan crawling menggunakan satu proses sebagai baseline.

**B. Local Parallel Processing**

Menjalankan multiprocessing pada satu komputer dengan beberapa process.

**C. Distributed Processing**

Menjalankan crawling menggunakan Master dan sejumlah Worker melalui jaringan.

**D. Dynamic Load Balancing**

Membandingkan static scheduling dengan dynamic load balancing.

**E. Fault Tolerance**

Melakukan simulasi kegagalan Worker dan mengukur kemampuan pemulihan task.

**F. Scalability Testing**

Menjalankan pengujian menggunakan:

- 1 Worker.
- 2 Workers.
- 4 Workers.
- 6 Workers.
- 9 Workers.

Setiap pengujian harus menggunakan konfigurasi workload yang dapat dibandingkan.

### Performance Metrics

| Metric             | Definisi                                        |
| ------------------ | ----------------------------------------------- |
| Execution Time     | Total waktu menyelesaikan pekerjaan             |
| Speedup            | Perbandingan waktu sequential terhadap parallel |
| Efficiency         | Efektivitas penggunaan jumlah Worker            |
| Throughput         | Jumlah halaman atau task per detik              |
| CPU Utilization    | Persentase penggunaan CPU                       |
| Memory Utilization | Penggunaan RAM                                  |
| Recovery Time      | Waktu pemulihan setelah kegagalan Worker        |

### Formula

**Speedup**

S = T sequential / T parallel

**Efficiency**

E = (Speedup / Number of Workers) × 100%

**Throughput**

Throughput = Successful Pages / Execution Time

**Recovery Time**

Recovery Time = Task Recovery Completion Time − Failure Detection Time

Semua hasil pengujian harus disimpan dalam Experiment History.

---

# 7. GUI / USER EXPERIENCE REQUIREMENTS

## 7.1 Design Principles

Antarmuka CrawlMesh harus memenuhi prinsip:

1. GUI-first operation.
2. Minimal manual configuration.
3. Clear system status.
4. Real-time monitoring.
5. Visual representation of distributed nodes.
6. One-click node management.
7. Easy performance comparison.

Pengguna tidak perlu menjalankan perintah terminal untuk mengoperasikan crawling dan mengelola cluster setelah Worker Agent terpasang.

## 7.2 Main Navigation

Sidebar aplikasi:

1. Overview.
2. Cluster Management.
3. Node Discovery.
4. Crawl Jobs.
5. Task Monitor.
6. Results Explorer.
7. Performance Lab.
8. Experiment History.
9. Settings.

## 7.3 Page 1 — Overview Dashboard

Menampilkan ringkasan kondisi cluster.

Komponen:

- Total Nodes.
- Active Workers.
- Offline Workers.
- Total CPU Cores.
- Total Pages Crawled.
- Current Throughput.
- Running Jobs.
- Recent Activities.

## 7.4 Page 2 — Node Discovery

Halaman untuk menemukan dan mendaftarkan Worker.

Komponen utama:

**Discover Network Nodes**

Tombol:

[ SCAN NETWORK ]

Hasil scan ditampilkan dalam bentuk node cards.

Contoh:

```
+----------------------------------+
| Worker-01                       |
| IP: 192.168.1.101                |
| CPU: 8 Cores                     |
| RAM: 16 GB                       |
| Status: Available                |
|                                  |
| [ ASSIGN AS WORKER ]             |
+----------------------------------+

+----------------------------------+
| Worker-02                       |
| IP: 192.168.1.102                |
| CPU: 4 Cores                     |
| RAM: 8 GB                        |
| Status: Available                |
|                                  |
| [ ASSIGN AS WORKER ]             |
+----------------------------------+
```

Setelah berhasil didaftarkan, tombol berubah menjadi:

[ WORKER ACTIVE ]

Pengguna juga dapat memilih beberapa node sekaligus untuk didaftarkan.

## 7.5 Page 3 — Cluster Topology

Halaman untuk memperlihatkan hubungan antar-node secara visual.

Contoh:

```
                 MASTER
                   |
        +----------+----------+
        |          |          |
      W-01       W-02       W-03
        |          |          |
      W-04       W-05       W-06
        |          |          |
      W-07       W-08       W-09
```

Setiap node dapat diklik untuk melihat:

- IP Address.
- CPU.
- Memory.
- Process Count.
- Active Tasks.
- Completed Tasks.
- Connection Status.

Visualisasi ini membantu pengguna memahami topologi sistem terdistribusi.

## 7.6 Page 4 — Crawl Job

Halaman untuk membuat pekerjaan crawling.

Tersedia form konfigurasi:

- Job Name.
- Seed URL.
- Maximum Pages.
- Maximum Depth.
- Allowed Domains.
- Batch Size.
- Request Delay.
- Robots.txt.

Tombol:

- Start.
- Pause.
- Resume.
- Cancel.

## 7.7 Page 5 — Live Task Monitor

Menampilkan distribusi task kepada seluruh Worker.

Contoh:

| Worker | Assigned | Completed | Failed | Status |
| ------ | -------- | --------- | ------ | ------ |
| W1     | 30       | 28        | 2      | Busy   |
| W2     | 25       | 25        | 0      | Idle   |
| W3     | 35       | 30        | 5      | Busy   |
| W4     | 20       | 18        | 2      | Busy   |

Informasi diperbarui secara berkala.

## 7.8 Page 6 — Results Explorer

Pengguna dapat melihat hasil crawling dalam bentuk tabel.

Fitur:

- Search URL.
- Filter HTTP Status.
- Filter Worker.
- Sort by Response Time.
- View Page Details.
- Export CSV.
- Export JSON.

## 7.9 Page 7 — Performance Lab

Halaman untuk melakukan eksperimen komputasi paralel.

Pengguna memilih:

- Experiment Type.
- Number of Workers.
- Dataset / Seed URL.
- Maximum Pages.
- Scheduling Strategy.

Tombol:

[ RUN EXPERIMENT ]

Hasil pengujian disajikan melalui tabel dan grafik.

## 7.10 Page 8 — Experiment History

Menyimpan riwayat eksperimen.

Contoh:

| Experiment     | Workers     | Execution Time | Speedup |
| -------------- | ----------- | -------------- | ------- |
| Sequential     | 1 Process   | -              | 1.00x   |
| Local Parallel | 4 Processes | -              | -       |
| Distributed    | 2           | -              | -       |
| Distributed    | 4           | -              | -       |
| Distributed    | 6           | -              | -       |
| Distributed    | 9           | -              | -       |

Nilai performa diisi berdasarkan hasil pengujian aktual, bukan angka simulasi.

---

# 8. SYSTEM WORKFLOW

## 8.1 Initial Cluster Setup

1. Pengguna membuka CrawlMesh.
2. Pengguna menginisialisasi komputer pertama sebagai Master.
3. Master menghasilkan Cluster ID dan pairing token.
4. Worker Agent dijalankan pada komputer lainnya.
5. Worker melakukan registrasi menggunakan endpoint dan pairing token.
6. Pengguna menekan Discover Workers.
7. Master mendeteksi Worker yang tersedia.
8. Pengguna memilih Worker dan melakukan registrasi.
9. Dashboard menampilkan seluruh node.
10. Cluster siap digunakan.

## 8.2 Crawling Workflow

1. Pengguna membuat Crawl Job.
2. Pengguna memasukkan Seed URL.
3. Master memvalidasi konfigurasi.
4. Master membuat URL Frontier.
5. URL dipecah menjadi task.
6. Task Scheduler mencari Worker yang tersedia.
7. Load Balancer menentukan Worker tujuan.
8. Worker menerima task.
9. Worker melakukan crawling dan multiprocessing.
10. Worker mengirim hasil kepada Master.
11. Master menyimpan hasil dan melakukan deduplication.
12. URL baru dimasukkan ke Frontier.
13. Proses berulang hingga batas crawling terpenuhi.
14. Job dinyatakan selesai.
15. Hasil tersedia melalui GUI.

## 8.3 Fault Tolerance Workflow

1. Worker sedang memproses task.
2. Worker mengalami kegagalan.
3. Heartbeat tidak diterima oleh Master.
4. Master mengubah status Worker menjadi Offline.
5. Task yang belum selesai ditandai untuk recovery.
6. Task dimasukkan kembali ke queue.
7. Worker lain menerima task.
8. Task diproses ulang.
9. Hasil dikirim kepada Master.
10. Recovery Time dicatat.

---

# 9. NON-FUNCTIONAL REQUIREMENTS

## 9.1 Performance

- Task harus dapat didistribusikan ke beberapa Worker.
- Multiprocessing harus menggunakan lebih dari satu process ketika konfigurasi mengizinkan.
- Monitoring harus diperbarui secara berkala.
- Scheduler harus mampu menghindari pemberian task baru kepada Worker yang tidak sehat.

## 9.2 Reliability

- Task yang gagal tidak boleh hilang tanpa pencatatan.
- Sistem harus mendukung retry dan requeue.
- Hasil duplikat harus dapat dideteksi.
- Worker yang kembali online harus dapat melakukan registrasi ulang.

## 9.3 Usability

- Pengelolaan cluster dilakukan melalui GUI.
- Informasi status node harus mudah dipahami.
- Operasi utama dapat dilakukan melalui tombol.
- Error harus ditampilkan menggunakan pesan yang jelas.
- Pengguna dapat melihat aktivitas sistem tanpa membuka terminal.

## 9.4 Security

- Komunikasi Worker dan Master menggunakan autentikasi token.
- Endpoint administrasi tidak boleh terbuka untuk akses tanpa otorisasi.
- Penggunaan HTTPS/TLS direkomendasikan.
- Crawling dibatasi pada domain yang diizinkan.
- Sistem harus menghormati robots.txt dan batas permintaan per domain.
- Private IP, localhost, link-local, dan alamat jaringan internal harus diblokir sebagai target crawling secara default untuk mencegah SSRF.
- Sistem tidak melakukan bypass autentikasi, CAPTCHA, atau mekanisme proteksi website.

## 9.5 Compatibility

- Worker dapat berjalan pada komputer yang saling terhubung melalui jaringan.
- Setiap Worker mendukung multiprocessing.
- Sistem mendukung konfigurasi jaringan LAN kabel maupun wireless.
- GUI dapat diakses melalui browser.

---

# 10. DATA MANAGEMENT

Sistem setidaknya membutuhkan entitas data berikut:

## 10.1 Node

Menyimpan identitas dan informasi setiap komputer.

Field:

- node_id
- hostname
- ip_address
- role
- cpu_cores
- memory_total
- status
- last_heartbeat

## 10.2 Crawl Job

Menyimpan konfigurasi pekerjaan crawling.

Field:

- job_id
- job_name
- seed_urls
- allowed_domains
- maximum_pages
- maximum_depth
- status
- created_at
- completed_at

## 10.3 Crawl Task

Menyimpan pekerjaan yang didistribusikan.

Field:

- task_id
- job_id
- assigned_worker
- urls
- status
- attempt_count
- started_at
- completed_at

## 10.4 Crawl Result

Menyimpan hasil crawling.

Field:

- result_id
- task_id
- url
- title
- extracted_text
- http_status
- content_hash
- response_time
- worker_id
- crawled_at

## 10.5 Worker Metrics

Menyimpan informasi resource Worker.

Field:

- metric_id
- worker_id
- cpu_usage
- memory_usage
- active_processes
- active_tasks
- throughput
- recorded_at

## 10.6 Experiment

Menyimpan hasil pengujian performa.

Field:

- experiment_id
- experiment_type
- worker_count
- execution_time
- speedup
- efficiency
- throughput
- cpu_utilization
- memory_utilization
- recovery_time
- created_at

---

# 11. RECOMMENDED TECHNOLOGY STACK

Teknologi berikut merupakan rekomendasi implementasi, bukan ketentuan wajib dari soal.

| Layer           | Recommended Technology                       | Purpose                      |
| --------------- | -------------------------------------------- | ---------------------------- |
| Frontend        | React + TypeScript                           | GUI                          |
| UI Styling      | Tailwind CSS                                 | Interface                    |
| Backend Master  | Python + FastAPI                             | API dan orchestration        |
| Worker Agent    | Python                                       | Crawling agent               |
| Multiprocessing | Python multiprocessing / ProcessPoolExecutor | Parallel execution           |
| Task Queue      | Redis                                        | Task distribution            |
| Database        | PostgreSQL                                   | Persistent storage           |
| HTML Parsing    | BeautifulSoup / lxml                         | Content extraction           |
| Communication   | HTTP + WebSocket                             | Master–Worker communication |
| Monitoring      | psutil                                       | CPU dan memory monitoring    |
| Deployment      | Docker / Native Service                      | Service deployment           |

Arsitektur teknologi dapat disesuaikan dengan kemampuan komputer laboratorium dan kondisi jaringan.

---

# 12. ACCEPTANCE CRITERIA

Fitur dinyatakan memenuhi kebutuhan apabila kriteria berikut berhasil dibuktikan.

| ID    | Acceptance Criteria    | Expected Result                                 |
| ----- | ---------------------- | ----------------------------------------------- |
| AC-01 | Master initialization  | Master berhasil diinisialisasi                  |
| AC-02 | Node discovery         | Worker Agent ditemukan melalui GUI              |
| AC-03 | Role identification    | Master dan Worker memiliki identitas yang benar |
| AC-04 | Node registration      | 9 Worker berhasil terdaftar                     |
| AC-05 | Heartbeat              | Status Worker dapat dipantau                    |
| AC-06 | Task decomposition     | URL berhasil dipecah menjadi beberapa task      |
| AC-07 | Multiprocessing        | Worker menjalankan beberapa process             |
| AC-08 | Distributed processing | Task diproses oleh beberapa komputer            |
| AC-09 | Dynamic load balancing | Alokasi task menyesuaikan beban Worker          |
| AC-10 | Fault detection        | Worker yang gagal terdeteksi                    |
| AC-11 | Task recovery          | Task gagal berhasil di-requeue                  |
| AC-12 | Result aggregation     | Hasil crawling terkumpul di Master              |
| AC-13 | Performance monitoring | Metrik resource tersedia                        |
| AC-14 | Benchmarking           | Sequential dan parallel dapat dibandingkan      |
| AC-15 | Scalability            | Pengujian 1, 2, 4, 6, dan 9 Worker berjalan     |
| AC-16 | Export                 | Hasil crawling dan eksperimen dapat diekspor    |

---

# 13. TESTING AND PERFORMANCE EVALUATION PLAN

Pengujian menjadi bagian penting karena sistem tidak hanya dituntut berjalan, tetapi juga harus memperlihatkan manfaat komputasi paralel dan sistem terdistribusi.

## 13.1 Sequential Processing Test

Tujuan:
Mengukur waktu pemrosesan menggunakan satu process sebagai baseline.

Konfigurasi:

- Satu komputer.
- Satu process.
- Dataset atau seed URL yang sama.
- Batas crawling yang sama.

Output:

- Execution Time.
- Throughput.
- CPU Utilization.
- Memory Utilization.

## 13.2 Local Parallel Processing Test

Tujuan:
Mengukur peningkatan performa melalui multiprocessing dalam satu komputer.

Konfigurasi:

- Satu komputer.
- Beberapa process.
- Dataset yang sama dengan pengujian sequential.

Output:

- Execution Time.
- Speedup.
- Efficiency.
- CPU Utilization.
- Memory Utilization.

## 13.3 Distributed Processing Test

Tujuan:
Membuktikan distribusi pekerjaan melalui jaringan.

Konfigurasi:

- 1 Master.
- Beberapa Worker.
- Task didistribusikan melalui jaringan.

Output:

- Execution Time.
- Throughput.
- Worker Distribution.
- CPU Utilization.
- Memory Utilization.

## 13.4 Dynamic Load Balancing Test

Tujuan:
Membandingkan distribusi pekerjaan sebelum dan sesudah mekanisme dynamic load balancing.

Skenario:

1. Jalankan crawling dengan static scheduling.
2. Catat distribusi task setiap Worker.
3. Jalankan crawling dengan dynamic scheduling.
4. Catat kembali distribusi task.
5. Bandingkan penggunaan resource dan waktu penyelesaian.

## 13.5 Fault Tolerance Test

Tujuan:
Menguji kemampuan sistem dalam menangani Worker failure.

Skenario:

1. Jalankan crawling pada beberapa Worker.
2. Pilih salah satu Worker.
3. Hentikan Worker Agent atau putuskan koneksinya.
4. Amati perubahan status.
5. Amati proses requeue.
6. Pastikan Worker lain mengambil alih task.
7. Catat Recovery Time.

## 13.6 Scalability Test

Jumlah Worker yang diuji:

| Experiment | Master | Worker |
| ---------- | ------ | ------ |
| Test 1     | 1      | 1      |
| Test 2     | 1      | 2      |
| Test 3     | 1      | 4      |
| Test 4     | 1      | 6      |
| Test 5     | 1      | 9      |

Setiap pengujian harus menggunakan workload yang sama agar hasil perbandingan valid.

## 13.7 Experimental Control

Agar hasil pengujian dapat dipertanggungjawabkan:

- Gunakan dataset atau kumpulan halaman yang sama.
- Tetapkan batas crawling yang sama.
- Gunakan konfigurasi request yang sama.
- Catat spesifikasi hardware setiap node.
- Catat kondisi jaringan.
- Lakukan pengulangan pengujian.
- Bandingkan hasil berdasarkan pengukuran aktual.
- Pisahkan pengaruh network latency dari peningkatan performa komputasi apabila memungkinkan.

Disarankan menggunakan website pengujian yang dikelola sendiri sebagai sumber utama benchmark agar konten, ukuran halaman, dan respons server lebih konsisten.

---

# 14. PROJECT DEVELOPMENT PHASES

## Phase 1 — Foundation

Target:

- Inisialisasi Master.
- Implementasi Worker Agent.
- Komunikasi jaringan.
- Registrasi node.
- Heartbeat.

Deliverable:
Cluster Master–Worker dapat terbentuk.

## Phase 2 — GUI and Node Management

Target:

- Dashboard.
- Node Discovery.
- Role Identification.
- Worker Registration.
- Cluster Topology.

Deliverable:
Pengguna dapat mengelola cluster melalui GUI.

## Phase 3 — Distributed Web Crawling

Target:

- URL Frontier.
- Task Decomposition.
- Task Scheduler.
- HTTP Fetching.
- HTML Parsing.
- Result Aggregation.

Deliverable:
Crawling dapat berjalan melalui beberapa Worker.

## Phase 4 — Parallel Processing

Target:

- Multiprocessing.
- Process Pool Management.
- Resource Monitoring.

Deliverable:
Setiap Worker dapat menggunakan multicore CPU.

## Phase 5 — Dynamic Load Balancing

Target:

- Resource-based scheduling.
- Worker load evaluation.
- Dynamic task allocation.

Deliverable:
Distribusi pekerjaan menyesuaikan kondisi Worker.

## Phase 6 — Fault Tolerance

Target:

- Heartbeat failure detection.
- Task retry.
- Task requeue.
- Worker recovery.

Deliverable:
Sistem dapat menangani kegagalan Worker.

## Phase 7 — Performance Evaluation

Target:

- Sequential benchmark.
- Local parallel benchmark.
- Distributed benchmark.
- Dynamic load balancing comparison.
- Fault tolerance test.
- Scalability test.

Deliverable:
Laporan pengukuran dan analisis performa.

## Phase 8 — Finalization

Target:

- Bug fixing.
- Validasi seluruh fitur.
- Dokumentasi.
- Deployment.
- Perekaman demonstrasi.

Deliverable:
Sistem final dan seluruh kebutuhan pengumpulan UAS.

---

# 15. RISKS AND MITIGATION

| Risiko                    | Dampak                      | Mitigasi                                                |
| ------------------------- | --------------------------- | ------------------------------------------------------- |
| Worker tidak ditemukan    | Cluster tidak lengkap       | Sediakan pairing token dan manual IP discovery          |
| Network latency tinggi    | Crawling lambat             | Monitoring jaringan dan pengaturan timeout              |
| Worker overload           | Task tidak seimbang         | Dynamic load balancing                                  |
| Worker disconnected       | Task gagal                  | Heartbeat dan requeue                                   |
| Duplicate URL             | Pemrosesan berulang         | URL normalization dan deduplication                     |
| Website membatasi request | Crawling gagal              | Respect robots.txt dan domain delay                     |
| Master failure            | Seluruh koordinasi terhenti | Dokumentasikan sebagai batasan arsitektur single-master |
| Multiprocessing overhead  | Efisiensi menurun           | Konfigurasi jumlah process berdasarkan CPU              |
| Resource heterogeneity    | Beban tidak seimbang        | Resource-aware scheduling                               |

---

# 16. DEFINITION OF DONE

CrawlMesh dianggap selesai apabila:

1. Master dapat dijalankan dan dikelola melalui GUI.
2. Sistem dapat mendeteksi dan mendaftarkan 9 Worker.
3. Seluruh Worker dapat berkomunikasi dengan Master.
4. Setiap Worker mendukung multiprocessing.
5. Crawling dapat dijalankan secara distributed.
6. Task dapat dibagi dan didistribusikan secara otomatis.
7. Dynamic load balancing dapat dibuktikan.
8. Fault tolerance dapat dibuktikan melalui simulasi kegagalan Worker.
9. Seluruh hasil crawling dapat dikumpulkan.
10. Metrik performa dapat dihasilkan.
11. Pengujian scalability dapat dilakukan.
12. Sistem dapat didemonstrasikan menggunakan minimal 10 komputer fisik.

---

# 17. FINAL PROJECT DELIVERABLES

## 17.1 Application

Aplikasi CrawlMesh yang terdiri atas:

- Master Application.
- Worker Agent.
- Web GUI.
- Task Scheduler.
- Multiprocessing Engine.
- Load Balancer.
- Fault Tolerance Module.
- Performance Evaluation Module.

## 17.2 Source Code

Source code terkompresi yang mencakup:

- Program Master.
- Program Worker.
- Komunikasi jaringan.
- Task distribution.
- Multiprocessing.
- Dynamic load balancing.
- Fault tolerance.
- Performance measurement.

## 17.3 Project Report

Dokumentasi laporan disusun berdasarkan struktur yang diminta dalam UAS:

**BAB I — Pendahuluan**

- Latar Belakang.
- Tujuan.

**BAB II — Studi Pustaka**

- Distributed Computing.
- Master–Worker Architecture.
- Parallel Processing.
- Multiprocessing.
- Web Crawling.
- Task Scheduling.
- Dynamic Load Balancing.
- Fault Tolerance.

**BAB III — Metodologi**

- Rancangan Percobaan.
- Arsitektur Sistem.
- Topologi Jaringan.
- Mekanisme Kerja.
- Konfigurasi Node.
- Konfigurasi Jaringan.

**BAB IV — Hasil dan Pembahasan**

- Implementasi Sistem.
- Hasil Sequential Processing.
- Hasil Local Parallel Processing.
- Hasil Distributed Processing.
- Hasil Dynamic Load Balancing.
- Hasil Fault Tolerance.
- Hasil Scalability.
- Analisis Metrik.

**Kesimpulan**

## 17.4 Video Demonstration

Video demonstrasi maksimal 5 menit yang memperlihatkan:

1. Master initialization.
2. Worker discovery melalui GUI.
3. Registrasi 9 Worker.
4. Cluster topology.
5. Crawling execution.
6. Distribusi task.
7. Multiprocessing.
8. Simulasi Worker failure.
9. Task recovery.
10. Performance dashboard.

Demonstrasi harus menggunakan minimal 10 node fisik sesuai ketentuan UAS.

---

# 18. PRODUCT SUCCESS DEFINITION

Keberhasilan CrawlMesh tidak hanya ditentukan oleh kemampuannya mengambil informasi dari halaman web.

Keberhasilan utama produk ditentukan oleh kemampuannya menunjukkan bahwa:

1. Satu pekerjaan besar dapat dipecah menjadi beberapa task independen.
2. Task dapat dikerjakan secara bersamaan oleh sejumlah Worker.
3. Setiap Worker mampu menggunakan multiprocessing.
4. Master dapat mendistribusikan pekerjaan berdasarkan kondisi aktual Worker.
5. Kegagalan satu Worker tidak menyebabkan hilangnya seluruh pekerjaan.
6. Performa sistem dapat diukur dan dibandingkan.
7. Seluruh proses dapat dikendalikan dan diamati melalui GUI.

Dengan demikian, CrawlMesh menjadi implementasi nyata dari konsep komputasi paralel dan sistem terdistribusi menggunakan kasus Distributed Web Crawler.

**END OF DOCUMENT**

## **19. Catatan keputusan desain yang penting**

Ada tiga keputusan arsitektur yang sebaiknya dipertahankan saat PRD ini diterjemahkan menjadi aplikasi.

**1. GUI harus menjadi pusat orkestrasi, bukan sekadar dashboard.**

Pengguna harus bisa melakukan discovery, registrasi Worker, menjalankan crawling, memantau distribusi task, dan menguji kegagalan melalui GUI. Ini yang membedakan produk dari crawler biasa yang hanya memiliki halaman monitoring.

**2. Jangan mengabaikan multiprocessing karena crawling bersifat I/O-bound.**

Web crawling memang banyak menunggu respons jaringan. Agar persyaratan multicore CPU benar-benar terpenuhi, Worker perlu memiliki proses paralel untuk parsing HTML, ekstraksi konten, normalisasi URL, dan pemrosesan metadata. Jadi, bukan sekadar menjalankan banyak HTTP request secara bersamaan.

**3. Benchmarking harus menjadi fitur bawaan aplikasi.**

Jangan sampai setelah aplikasi selesai dibuat, Anda masih harus membuat program tambahan hanya untuk menghitung speedup, efficiency, throughput, dan recovery time.

Semua pengujian sebaiknya dapat dilakukan melalui Performance Lab dan hasilnya tersimpan otomatis.

## **20. Rekomendasi prioritas implementasi**

Jika melihat keseluruhan kebutuhan UAS, urutan pengerjaan paling aman adalah:

1. **Cluster Discovery**

   Master initialization, Worker Agent, deteksi node, dan registrasi Worker.

   Fondasi wajib
2. **Distributed Crawling Engine**

   URL frontier, task decomposition, task queue, komunikasi jaringan, dan hasil crawling.
3. **Multiprocessing Engine**

   Memastikan setiap Worker menggunakan multicore CPU.
4. **Dynamic Load Balancer**

   Distribusi task berdasarkan kondisi resource Worker.
5. **Fault Tolerance**

   Heartbeat, failure detection, retry, dan requeue.
6. **Performance Lab**

   Benchmark sequential, local parallel, distributed, dan scalability.
7. **GUI Refinement**

   Dashboard, visualisasi topologi, monitoring, dan export.

**Rekomendasi akhir:** pertahankan CrawlMesh sebagai satu aplikasi dengan dua komponen runtime utama, yaitu Master Application dan Worker Agent. React GUI terhubung ke Master, sedangkan Worker Agent berjalan sebagai service pada masing-masing komputer. Dengan pemisahan ini, GUI dapat mengelola cluster secara terpusat tanpa menjadikan setiap komputer harus menjalankan aplikasi frontend.

PRD ini sudah mencakup kebutuhan fungsional, arsitektur, UX, mekanisme komputasi, pengujian, dan deliverable UAS. Langkah pengembangan berikutnya yang paling tepat adalah menerjemahkan PRD ini menjadi technical design document (TDD), termasuk diagram komunikasi Master–Worker, struktur service, dan kontrak API sebelum implementasi dimulai.
