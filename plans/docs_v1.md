# **PRODUCT REQUIREMENTS DOCUMENT (PRD)**

## **AI Agent — Penyusunan Draft Laporan Proyek CrawlMesh**

Markdown Version

Version 1.1

**Nama Proyek:** CrawlMesh — Distributed Web Crawler
**Jenis Dokumen:** Product Requirements Document untuk AI Agent
**Bahasa Output:** Bahasa Indonesia formal akademik
**Format Output Agent:** Microsoft Word (`.docx`)
**Cakupan Pengerjaan:** BAB I–V dengan kedalaman berbeda sesuai tahap pengerjaan.

# **1. PROJECT OVERVIEW**

## **1.1 Latar Belakang**

CrawlMesh merupakan proyek pengembangan aplikasi Distributed Web Crawler menggunakan pendekatan komputasi paralel dan sistem terdistribusi berbasis arsitektur Master–Worker.

Proyek ini dikembangkan sebagai pemenuhan tugas Ujian Akhir Semester (UAS) mata kuliah Komputasi Paralel dan Sistem Terdistribusi.

Sistem dirancang untuk mendistribusikan pekerjaan crawling halaman web kepada beberapa Worker sehingga proses pengambilan informasi dapat dilakukan secara paralel dan terdistribusi.

## **1.2 Tujuan Agent**

AI Agent bertugas menyusun draft laporan proyek CrawlMesh berdasarkan:

1. Dokumen ketentuan UAS.
2. Source code dan struktur repository CrawlMesh.
3. Konfigurasi aplikasi dan infrastruktur.
4. Dokumentasi implementasi.
5. Screenshot aplikasi.
6. Log aktivitas dan hasil pengujian.
7. Data pengukuran performa.

Agent harus menghasilkan dokumen akademik yang memiliki struktur laporan jelas, pembahasan teknis yang akurat, dan keterlacakan terhadap bukti implementasi.

## **1.3 Output yang Diharapkan**

| Atribut   | Ketentuan                               |
| --------- | --------------------------------------- |
| Nama file | `Laporan_Proyek_CrawlMesh_Draft.docx` |
| Format    | Microsoft Word `.docx`                |
| Bahasa    | Indonesia                               |
| Gaya      | Formal akademik dan teknis              |
| BAB I     | Outline awal                            |
| BAB II    | Outline awal                            |
| BAB III   | Disusun lengkap                         |
| BAB IV    | Disusun sebagian berdasarkan bukti      |
| BAB V     | Outline awal                            |
| Referensi | Sumber aktual dan dapat diverifikasi    |

## **1.4 Prinsip Penyusunan**

Agent harus menerapkan prinsip berikut:

- Evidence-based writing: setiap klaim teknis harus memiliki sumber bukti.
- Technical accuracy: konfigurasi dan mekanisme harus sesuai implementasi aktual.
- Academic writing: menggunakan bahasa Indonesia formal.
- Reproducibility: metodologi dan pengukuran harus dapat direproduksi.
- Incremental documentation: laporan disusun agar mudah dikembangkan pada tahap berikutnya.

# **2. PROJECT CONTEXT DAN KETENTUAN UAS**

## **2.1 Tema Proyek**

Tema yang dipilih adalah:

**Tema 8 — Distributed Web Crawler**

Deskripsi pada dokumen UAS:

- Pengambilan informasi dari sejumlah halaman web.
- Pembagian tugas crawling kepada beberapa Worker.

## **2.2 Ketentuan Teknis UAS**

Berdasarkan dokumen UAS, sistem harus memenuhi persyaratan berikut.

| Komponen               | Persyaratan                                                  |
| ---------------------- | ------------------------------------------------------------ |
| Arsitektur             | Master–Worker                                               |
| Jumlah node fisik      | Minimal 10 komputer                                          |
| Master                 | 1 node                                                       |
| Worker                 | 9 node                                                       |
| Parallel Processing    | Multiprocessing dan multicore CPU                            |
| Distributed Processing | Komunikasi jaringan, distribusi pekerjaan, pengumpulan hasil |
| Dynamic Load Balancing | Distribusi dinamis berdasarkan kondisi dan kemampuan Worker  |
| Fault Tolerance        | Deteksi kegagalan Worker dan retry/requeue/pemulihan         |
| Performance Evaluation | Pengukuran dan analisis performa                             |

## **2.3 Pengujian yang Wajib Dibahas**

| ID     | Jenis Pengujian           | Tujuan                                                       |
| ------ | ------------------------- | ------------------------------------------------------------ |
| EXP-01 | Sequential Processing     | Menjadi baseline pengukuran                                  |
| EXP-02 | Local Parallel Processing | Mengukur multiprocessing pada satu komputer                  |
| EXP-03 | Distributed Processing    | Mengukur pemrosesan menggunakan beberapa Worker              |
| EXP-04 | Dynamic Load Balancing    | Membandingkan distribusi beban sebelum dan sesudah mekanisme |
| EXP-05 | Fault Tolerance           | Menguji kegagalan Worker dan pemulihan task                  |
| EXP-06 | Scalability               | Menguji variasi jumlah Worker                                |

Variasi jumlah Worker untuk pengujian scalability:

- 1 Worker
- 2 Workers
- 4 Workers
- 6 Workers
- 9 Workers

## **2.4 Metrik Evaluasi**

| Metrik             | Keterangan                                    |
| ------------------ | --------------------------------------------- |
| Execution Time     | Waktu penyelesaian pekerjaan                  |
| Speedup            | Perbandingan kecepatan terhadap baseline      |
| Efficiency         | Efisiensi penggunaan unit pemrosesan paralel  |
| Throughput         | Jumlah halaman yang diproses per satuan waktu |
| CPU Utilization    | Pemanfaatan CPU                               |
| Memory Utilization | Pemanfaatan memori                            |
| Recovery Time      | Waktu pemulihan setelah kegagalan Worker      |

## **2.5 Hierarki Sumber Informasi**

Agent harus menggunakan urutan sumber berikut:

1. Dokumen UAS sebagai sumber persyaratan.
2. Source code dan repository sebagai sumber implementasi.
3. File konfigurasi sebagai sumber konfigurasi aktual.
4. Log dan hasil eksperimen sebagai sumber pengukuran.
5. Screenshot sebagai bukti visual.
6. Dokumentasi resmi teknologi sebagai sumber teori dan referensi teknis.
7. PRD atau rancangan proyek sebagai sumber informasi desain, bukan bukti implementasi.

**Ketentuan:** Agent tidak boleh menganggap fitur yang tercantum dalam rancangan sebagai fitur yang sudah berhasil diimplementasikan.

# **3. SCOPE OF WORK**

## **3.1 Pembagian Cakupan Laporan**

Laporan disusun dalam lima bagian utama.

| Bagian                       | Tahap            | Status        |
| ---------------------------- | ---------------- | ------------- |
| BAB I. Pendahuluan           | Tahap berikutnya | Outline awal  |
| BAB II. Studi Pustaka        | Tahap berikutnya | Outline awal  |
| BAB III. Metodologi          | Tahap sekarang   | Full Draft    |
| BAB IV. Hasil dan Pembahasan | Tahap sekarang   | Partial Draft |
| BAB V. Kesimpulan            | Tahap berikutnya | Outline awal  |

## **3.2 Batasan Tahap Pengerjaan**

Agent harus:

1. Menyusun BAB III secara lengkap.
2. Menyusun BAB IV bagian implementasi berdasarkan kondisi aktual.
3. Menyiapkan struktur hasil pengukuran.
4. Mengisi hasil pengukuran hanya jika data tersedia.
5. Menyusun analisis hanya berdasarkan hasil pengukuran yang valid.
6. Menyediakan outline awal untuk BAB I, BAB II, dan BAB V.

Agent tidak perlu mengembangkan isi BAB I, BAB II, dan BAB V menjadi pembahasan lengkap pada tahap ini.

## **3.3 Batasan Konteks**

Agent hanya menggunakan sumber yang diberikan dalam sesi pengerjaan aktif dan file proyek yang secara eksplisit tersedia.

Agent tidak boleh mengasumsikan informasi dari percakapan lain, memory, atau sumber yang tidak dapat diakses.

# **4. WORKFLOW WAJIB AGENT**

Agent harus mengikuti tahapan berikut secara berurutan.

| Tahap | Aktivitas                                        | Output                   |
| ----- | ------------------------------------------------ | ------------------------ |
| 1     | Inventarisasi seluruh file dan sumber informasi  | Source inventory         |
| 2     | Membaca dokumen UAS                              | Requirement mapping      |
| 3     | Discovery seluruh skill yang relevan dengan DOCX | Skill inventory          |
| 4     | Membaca instruksi dan referensi setiap skill     | Skill execution plan     |
| 5     | Memeriksa repository dan source code             | Implementation inventory |
| 6     | Memeriksa konfigurasi dan topologi               | Infrastructure inventory |
| 7     | Memeriksa screenshot, log, dan hasil eksperimen  | Evidence inventory       |
| 8     | Menyusun outline seluruh BAB                     | Report structure         |
| 9     | Menyusun BAB III                                 | Full methodology draft   |
| 10    | Menyusun BAB IV                                  | Partial results draft    |
| 11    | Menyiapkan placeholder BAB I, II, dan V          | Initial outline          |
| 12    | Melakukan validasi isi dan data                  | Validation report        |
| 13    | Membuat dokumen DOCX                             | Final draft document     |
| 14    | Melakukan pemeriksaan dokumen                    | QA report                |

## **4.1 Repository Inspection**

Agent harus memeriksa:

- Struktur direktori.
- Source code Master.
- Source code Worker.
- Modul komunikasi jaringan.
- Modul task distribution.
- Modul scheduling.
- Modul load balancing.
- Modul fault tolerance.
- Modul crawling.
- Modul penyimpanan hasil.
- Modul monitoring.
- Modul benchmark atau performance evaluation.
- File konfigurasi dan deployment.

Setiap fitur harus diberi status:

| Status      | Makna                                            |
| ----------- | ------------------------------------------------ |
| Implemented | Sudah ditemukan implementasi dan bukti pendukung |
| Partial     | Sebagian mekanisme sudah tersedia                |
| Planned     | Baru berupa rancangan                            |
| Not Found   | Tidak ditemukan dalam sumber yang diperiksa      |
| Unverified  | Belum dapat dipastikan                           |

# **5. OUTLINE LAPORAN PROYEK**

Bagian ini merupakan struktur induk dokumen yang harus digunakan agent.

**STRUKTUR LAPORAN CRAWLMESH**

Outline awal

**BAB I. PENDAHULUAN**

- 1.1 Latar Belakang
- 1.2 Tujuan

Outline awal

**BAB II. STUDI PUSTAKA**

- 2.1 Landasan Teori
- 2.2 Konsep dan Teknologi Pendukung (pengembangan)

Full Draft

**BAB III. METODOLOGI**

- 3.1 Rancangan Percobaan
- 3.2 Arsitektur Sistem dan Topologi
- 3.3 Mekanisme Kerja
- 3.4 Konfigurasi Node dan Jaringan

Partial Draft

**BAB IV. HASIL DAN PEMBAHASAN**

- 4.1 Implementasi
- 4.2 Hasil Pengukuran
- 4.3 Analisis Data

Outline awal

**BAB V. KESIMPULAN**

- 5.1 Kesimpulan
- 5.2 Saran (pengembangan)

# **6. SPESIFIKASI ISI BAB I — PENDAHULUAN**

Outline awal — dikembangkan pada tahap berikutnya

Agent harus membuat heading dan kerangka awal untuk BAB I tanpa menulis pembahasan panjang.

## **6.1 1.1 Latar Belakang**

Outline pembahasan:

1. Perkembangan kebutuhan pengambilan dan pengolahan informasi dari halaman web.
2. Tantangan proses web crawling ketika jumlah halaman yang diproses semakin besar.
3. Keterbatasan pendekatan pemrosesan secara sequential.
4. Konsep pemanfaatan komputasi paralel untuk meningkatkan efisiensi pemrosesan.
5. Konsep sistem terdistribusi menggunakan arsitektur Master–Worker.
6. Kebutuhan dynamic load balancing dan fault tolerance pada pemrosesan terdistribusi.
7. Alasan pemilihan Distributed Web Crawler sebagai tema proyek.
8. Gambaran umum solusi CrawlMesh.

**Arah pembahasan:** Menjelaskan permasalahan, kebutuhan, dan alasan pengembangan CrawlMesh.

## **6.2 1.2 Tujuan**

Outline tujuan:

1. Mengembangkan aplikasi Distributed Web Crawler berbasis Master–Worker.
2. Menerapkan task decomposition pada proses crawling.
3. Menerapkan parallel processing menggunakan multiprocessing.
4. Menerapkan distributed processing melalui komunikasi jaringan.
5. Mengimplementasikan dynamic load balancing.
6. Mengimplementasikan fault tolerance.
7. Mengevaluasi performa melalui pengujian sequential, local parallel, dan distributed processing.
8. Menganalisis scalability berdasarkan variasi jumlah Worker.

Catatan: tujuan final harus disesuaikan dengan fitur yang benar-benar dikembangkan dan diuji.

# **7. SPESIFIKASI ISI BAB II — STUDI PUSTAKA**

Outline awal — dikembangkan pada tahap berikutnya

## **7.1 2.1 Landasan Teori**

Agent harus menyiapkan struktur teori yang mendukung implementasi CrawlMesh.

Subbagian yang disarankan:

### **2.1.1 Web Crawling**

- Pengertian web crawling.
- Cara kerja web crawler.
- URL frontier.
- URL discovery.
- URL deduplication.
- HTTP request dan response.
- HTML parsing.
- Pengambilan informasi dari halaman web.

### **2.1.2 Komputasi Paralel**

- Pengertian komputasi paralel.
- Sequential processing.
- Parallel processing.
- Multicore processing.
- Multiprocessing.
- Task decomposition.

### **2.1.3 Sistem Terdistribusi**

- Pengertian sistem terdistribusi.
- Karakteristik sistem terdistribusi.
- Arsitektur Master–Worker.
- Komunikasi antar-node.
- Distribusi dan agregasi pekerjaan.

### **2.1.4 Dynamic Load Balancing**

- Pengertian load balancing.
- Static load balancing.
- Dynamic load balancing.
- Scheduling task.
- Resource-aware scheduling.

### **2.1.5 Fault Tolerance**

- Pengertian fault tolerance.
- Heartbeat mechanism.
- Failure detection.
- Task retry.
- Task requeue.
- Recovery mechanism.

### **2.1.6 Evaluasi Performa**

- Execution Time.
- Speedup.
- Efficiency.
- Throughput.
- CPU Utilization.
- Memory Utilization.
- Recovery Time.
- Scalability.

## **7.2 2.2 Konsep dan Teknologi Pendukung**

Bagian ini merupakan subbagian tambahan yang dapat dikembangkan jika relevan dengan teknologi aktual.

Contoh:

- Bahasa pemrograman yang digunakan.
- Framework atau library crawling.
- Protokol komunikasi.
- Database atau penyimpanan.
- Teknologi monitoring.
- Teknologi deployment.
- Tools pengujian performa.

Agent hanya boleh memasukkan teknologi yang benar-benar ditemukan dalam repository atau konfigurasi.

## **7.3 Ketentuan Referensi BAB II**

- Gunakan dokumentasi resmi dan publikasi ilmiah.
- Prioritaskan jurnal, konferensi, buku akademik, dan dokumentasi resmi.
- Pastikan setiap teori memiliki sumber.
- Jangan membuat referensi fiktif.
- Catat DOI atau URL apabila tersedia.

# **8. SPESIFIKASI ISI BAB III — METODOLOGI**

Wajib disusun lengkap pada tahap sekarang

BAB III merupakan bagian utama yang harus diselesaikan agent.

## **8.1 3.1 Rancangan Percobaan**

Bagian ini menjelaskan bagaimana sistem CrawlMesh dirancang untuk diuji dan dievaluasi.

### **8.1.1 Tujuan Percobaan**

Menjelaskan tujuan pengujian untuk mengetahui:

- Efektivitas pemrosesan paralel.
- Efektivitas pemrosesan terdistribusi.
- Pengaruh jumlah Worker terhadap performa.
- Efektivitas dynamic load balancing.
- Kemampuan pemulihan ketika Worker mengalami kegagalan.

### **8.1.2 Variabel Percobaan**

| Jenis            | Variabel                                                                      |
| ---------------- | ----------------------------------------------------------------------------- |
| Variabel bebas   | Mode pemrosesan dan jumlah Worker                                             |
| Variabel terikat | Execution Time, Speedup, Efficiency, Throughput, CPU, Memory, Recovery Time   |
| Variabel kontrol | Workload, URL, batas halaman, timeout, request delay, dan konfigurasi crawler |

### **8.1.3 Skenario Eksperimen**

Gunakan enam skenario yang telah ditentukan pada bagian 2.3.

Setiap skenario harus menjelaskan:

- Tujuan.
- Konfigurasi.
- Prosedur pengujian.
- Parameter.
- Metrik.
- Data yang dikumpulkan.

### **8.1.4 Rumus Metrik**

**Execution Time**

\\[ T = t\_{\text{finish}}-t\_{\text{start}} \\]

**Speedup**

\\[ S = \frac{T\_{\text{sequential}}}{T\_{\text{parallel}}} \\]

**Efficiency**

\\[ E = \frac{S}{P}\times100\\% \\]

Keterangan: \\(P\\) adalah jumlah process atau Worker sesuai konteks eksperimen.

**Throughput**

\\[ Throughput = \frac{\text{Successful Pages}}{\text{Execution Time}} \\]

**CPU Utilization**

Persentase penggunaan CPU berdasarkan hasil sampling selama eksperimen.

**Memory Utilization**

\\[ Memory(\\%) = \frac{\text{Used RAM}}{\text{Total RAM}}\times100\\% \\]

**Recovery Time**

\\[ T\_{\text{recovery}} = t\_{\text{task recovery selesai}}- t\_{\text{failure terdeteksi}} \\]

Agent harus menyesuaikan rumus dan definisi berdasarkan metode pengukuran aktual apabila berbeda.

## **8.2 3.2 Arsitektur Sistem dan Topologi**

Bagian ini menjelaskan desain arsitektur CrawlMesh.

Minimal harus memuat:

1. Gambaran arsitektur Master–Worker.
2. Diagram topologi jaringan.
3. Peran Master.
4. Peran Worker.
5. Mekanisme komunikasi.
6. Mekanisme distribusi task.
7. Mekanisme pengumpulan hasil.
8. Komponen penyimpanan.
9. Komponen monitoring.

Diagram harus menunjukkan hubungan komunikasi antara Master dan Worker serta alur data.

**Persyaratan khusus:** UAS mensyaratkan minimal 10 komputer fisik yang terdiri atas 1 Master dan 9 Worker. VM, container, dan process pada satu komputer tidak boleh otomatis dihitung sebagai komputer fisik terpisah.

## **8.3 3.3 Mekanisme Kerja**

Agent harus menjelaskan alur sistem berdasarkan implementasi aktual.

Outline:

1. Inisialisasi Master.
2. Inisialisasi Worker.
3. Discovery dan registrasi Worker.
4. Heartbeat dan monitoring node.
5. Pembuatan Crawl Job.
6. Pengelolaan URL frontier.
7. Task decomposition.
8. Distribusi task.
9. Eksekusi crawling oleh Worker.
10. Multiprocessing pada Worker.
11. Dynamic load balancing.
12. Fault tolerance.
13. Pengumpulan hasil.
14. Penyimpanan data crawling.

Gunakan flowchart atau sequence diagram jika dapat menggambarkan mekanisme sistem dengan lebih jelas.

## **8.4 3.4 Konfigurasi Node dan Jaringan**

### **8.4.1 Konfigurasi Node**

Siapkan tabel berikut.

| Node      | Role   | Hostname | IP     | OS     | CPU    | RAM    |
| --------- | ------ | -------- | ------ | ------ | ------ | ------ |
| Master-01 | Master | [Data]   | [Data] | [Data] | [Data] | [Data] |
| Worker-01 | Worker | [Data]   | [Data] | [Data] | [Data] | [Data] |
| Worker-02 | Worker | [Data]   | [Data] | [Data] | [Data] | [Data] |
| ...       | ...    | ...      | ...    | ...    | ...    | ...    |
| Worker-09 | Worker | [Data]   | [Data] | [Data] | [Data] | [Data] |

### **8.4.2 Konfigurasi Jaringan**

| Parameter           | Konfigurasi |
| ------------------- | ----------- |
| Media jaringan      | [Data]      |
| Subnet              | [Data]      |
| Gateway             | [Data]      |
| IP Master           | [Data]      |
| IP Worker           | [Data]      |
| Protokol komunikasi | [Data]      |
| Port                | [Data]      |
| Firewall            | [Data]      |
| DNS/Hostname        | [Data]      |

### **8.4.3 Konfigurasi Runtime**

Jelaskan:

- Bahasa pemrograman.
- Versi runtime.
- Library utama.
- Konfigurasi multiprocessing.
- Konfigurasi concurrency.
- Queue atau broker jika digunakan.
- Database jika digunakan.
- Environment variable nonrahasia.
- Command untuk menjalankan Master dan Worker.

Seluruh konfigurasi harus berasal dari implementasi aktual.

# **9. SPESIFIKASI ISI BAB IV — HASIL DAN PEMBAHASAN**

Partial Draft — hanya berdasarkan bukti aktual

## **9.1 4.1 Implementasi**

Bagian ini harus menjelaskan hasil pengembangan sistem CrawlMesh.

### **9.1.1 Implementasi Arsitektur Master**

Jelaskan:

- Inisialisasi Master.
- Registrasi Worker.
- Pengelolaan node.
- Task scheduling.
- Distribusi task.
- Monitoring.
- Pengumpulan hasil.

### **9.1.2 Implementasi Worker**

Jelaskan:

- Worker initialization.
- Heartbeat.
- Penerimaan task.
- Proses crawling.
- Multiprocessing.
- Pelaporan hasil.
- Resource monitoring.

### **9.1.3 Implementasi Task Distribution**

Jelaskan mekanisme pembagian pekerjaan dari Master kepada Worker.

### **9.1.4 Implementasi Dynamic Load Balancing**

Jelaskan:

- Parameter resource yang digunakan.
- Strategi pemilihan Worker.
- Mekanisme penjadwalan.
- Penanganan Worker overload.

### **9.1.5 Implementasi Fault Tolerance**

Jelaskan:

- Failure detection.
- Heartbeat timeout.
- Task retry.
- Task requeue.
- Recovery mechanism.

### **9.1.6 Implementasi Antarmuka**

Gunakan screenshot aktual untuk menjelaskan tampilan aplikasi.

Screenshot yang disarankan:

- Dashboard.
- Cluster monitoring.
- Worker discovery.
- Node topology.
- Crawl job configuration.
- Task monitoring.
- Hasil crawling.
- Performance evaluation.

### **9.1.7 Matriks Status Implementasi**

| Fitur              | Status   | Bukti             |
| ------------------ | -------- | ----------------- |
| Master             | [Status] | [Source code]     |
| Worker             | [Status] | [Source code]     |
| Discovery          | [Status] | [Log/Screenshot]  |
| Heartbeat          | [Status] | [Log]             |
| Task Distribution  | [Status] | [Log]             |
| Multiprocessing    | [Status] | [Source code]     |
| Load Balancing     | [Status] | [Source code/Log] |
| Fault Tolerance    | [Status] | [Log]             |
| Result Aggregation | [Status] | [Database/Log]    |
| Benchmark          | [Status] | [CSV/Log]         |

## **9.2 4.2 Hasil Pengukuran**

Bagian ini hanya dapat diisi jika eksperimen telah dilakukan dan datanya tersedia.

### **9.2.1 Hasil Sequential Processing**

Tampilkan konfigurasi dan hasil baseline.

### **9.2.2 Hasil Local Parallel Processing**

Tampilkan hasil multiprocessing pada satu komputer.

### **9.2.3 Hasil Distributed Processing**

Bandingkan hasil dengan variasi jumlah Worker.

| Worker | Execution Time | Speedup | Efficiency | Throughput |
| ------ | -------------- | ------- | ---------- | ---------- |
| 1      | [Data]         | [Data]  | [Data]     | [Data]     |
| 2      | [Data]         | [Data]  | [Data]     | [Data]     |
| 4      | [Data]         | [Data]  | [Data]     | [Data]     |
| 6      | [Data]         | [Data]  | [Data]     | [Data]     |
| 9      | [Data]         | [Data]  | [Data]     | [Data]     |

### **9.2.4 Hasil CPU dan Memory Utilization**

Tampilkan hasil pemakaian resource Master dan setiap Worker.

### **9.2.5 Hasil Dynamic Load Balancing**

Bandingkan distribusi task dan pemanfaatan resource sebelum dan sesudah mekanisme load balancing.

### **9.2.6 Hasil Fault Tolerance**

Tampilkan:

- Waktu Worker mengalami kegagalan.
- Waktu kegagalan terdeteksi.
- Jumlah task terdampak.
- Waktu requeue.
- Waktu task berhasil diselesaikan kembali.
- Recovery Time.

## **9.3 4.3 Analisis Data**

Analisis harus mencakup:

1. Perbandingan sequential dan local parallel.
2. Perbandingan local parallel dan distributed.
3. Pengaruh jumlah Worker terhadap execution time.
4. Analisis speedup.
5. Analisis efficiency.
6. Analisis throughput.
7. Analisis CPU dan memory utilization.
8. Analisis dynamic load balancing.
9. Analisis fault tolerance.
10. Identifikasi bottleneck dan keterbatasan sistem.

Agent harus membuat grafik hanya berdasarkan data aktual.

# **10. OUTLINE BAB V — KESIMPULAN**

Outline awal — dikembangkan setelah BAB IV selesai

BAB V merupakan bagian penutup laporan.

## **10.1 5.1 Kesimpulan**

Outline pembahasan:

1. Kesimpulan mengenai keberhasilan pengembangan CrawlMesh.
2. Kesimpulan mengenai implementasi arsitektur Master–Worker.
3. Kesimpulan mengenai penerapan parallel dan distributed processing.
4. Kesimpulan mengenai dynamic load balancing.
5. Kesimpulan mengenai fault tolerance.
6. Kesimpulan mengenai hasil evaluasi performa.
7. Kesimpulan mengenai scalability berdasarkan variasi jumlah Worker.

Kesimpulan harus menjawab tujuan yang ditetapkan pada BAB I.

## **10.2 5.2 Saran**

Bagian ini dapat ditambahkan sebagai pengembangan laporan.

Outline:

1. Optimalisasi algoritma scheduling.
2. Peningkatan efisiensi komunikasi jaringan.
3. Peningkatan mekanisme fault tolerance.
4. Optimalisasi pemanfaatan resource Worker.
5. Pengembangan monitoring dan observability.
6. Pengujian dengan workload yang lebih besar.

Saran harus didasarkan pada keterbatasan yang benar-benar ditemukan selama pengujian.

# **11. ATURAN PENGOLAHAN DATA DAN VALIDASI**

## **11.1 Validasi Data**

Agent harus memastikan:

- Jumlah halaman yang berhasil diproses benar.
- Jumlah task sesuai dengan log.
- Jumlah Worker sesuai konfigurasi aktual.
- Execution time menggunakan satuan yang konsisten.
- Speedup menggunakan baseline yang sama.
- Efficiency menggunakan nilai P yang tepat.
- Throughput dihitung dari halaman berhasil.
- Recovery Time menggunakan timestamp yang valid.

## **11.2 Larangan Rekayasa Data**

Agent tidak boleh:

- Mengarang hasil eksperimen.
- Membuat angka benchmark simulasi seolah-olah aktual.
- Mengarang konfigurasi jaringan.
- Mengklaim implementasi fitur tanpa bukti.
- Menganggap semua Worker memiliki spesifikasi identik.
- Mengubah hasil pengukuran agar terlihat lebih baik.
- Menghilangkan data yang tidak sesuai ekspektasi tanpa alasan metodologis.

## **11.3 Sistem Placeholder**

Gunakan placeholder yang konsisten:

| Placeholder               | Makna                            |
| ------------------------- | -------------------------------- |
| `[PERLU DATA]`          | Informasi belum diberikan        |
| `[BELUM DIUJI]`         | Pengujian belum dilakukan        |
| `[BELUM DIVERIFIKASI]`  | Informasi belum dapat dipastikan |
| `[MASUKKAN SCREENSHOT]` | Membutuhkan bukti visual         |
| `[MASUKKAN HASIL CSV]`  | Membutuhkan data pengukuran      |
| `[PERLU REFERENSI]`     | Membutuhkan sumber akademik      |

# **12. PERSYARATAN FORMAT DOCX**

## **12.1 Format Dokumen**

Output wajib berupa file:

`Laporan_Proyek_CrawlMesh_Draft.docx`

Jangan mengganti output utama dengan PDF, HTML, atau Markdown.

## **12.2 Format Akademik**

Jika tidak ada pedoman kampus yang diberikan, gunakan format sementara:

| Elemen          | Format          |
| --------------- | --------------- |
| Ukuran kertas   | A4              |
| Font            | Times New Roman |
| Ukuran font isi | 12 pt           |
| Spasi           | 1,5             |
| Alignment       | Justify         |
| Margin kiri     | 4 cm            |
| Margin kanan    | 3 cm            |
| Margin atas     | 3 cm            |
| Margin bawah    | 3 cm            |

Format tersebut harus disesuaikan apabila ditemukan pedoman resmi kampus.

## **12.3 Struktur Word**

Dokumen harus memiliki:

- Cover atau halaman judul sementara.
- Daftar isi otomatis.
- Heading 1, Heading 2, Heading 3.
- Nomor halaman.
- Header dan footer.
- Caption tabel.
- Caption gambar.
- Tabel editable.
- Diagram dan grafik.
- Daftar referensi jika sudah tersedia.

## **12.4 Penggunaan Gambar**

Gunakan gambar aktual dari proyek.

Setiap gambar harus memiliki:

- Nomor gambar.
- Judul/caption.
- Sumber.
- Penjelasan dalam paragraf.

Jangan menggunakan mockup sebagai bukti implementasi.

# **13. PERSYARATAN SKILL DAN TOOLING**

Bagian ini merupakan instruksi penting karena pengguna menginginkan agent memanfaatkan seluruh skill DOCX yang tersedia.

## **13.1 Skill Discovery**

Sebelum mengerjakan dokumen, agent wajib:

1. Memeriksa katalog seluruh skill yang tersedia.
2. Mengidentifikasi skill terkait DOCX, Word, document authoring, report writing, formatting, citation, dan document QA.
3. Membaca instruksi lengkap setiap skill yang relevan.
4. Membaca file referensi tambahan yang diwajibkan.
5. Mengikuti urutan pemanggilan skill dan tool sesuai instruksinya.

## **13.2 Prinsip Penggunaan Skill**

- Gunakan seluruh skill yang relevan dan kompatibel.
- Hindari penggunaan skill yang tidak berkaitan dengan pembuatan dokumen.
- Ikuti prasyarat dan routing setiap skill.
- Jangan mengklaim skill tertentu digunakan apabila tidak benar-benar dijalankan.
- Jika skill khusus DOCX tidak tersedia, gunakan library pembuat DOCX yang tersedia.

## **13.3 Tooling**

Agent dapat menggunakan:

- `python-docx` untuk pembuatan dokumen.
- Library diagram untuk arsitektur dan flowchart.
- Library grafik untuk visualisasi hasil pengukuran.
- Tool validasi dan rendering DOCX jika tersedia.

File hasil harus diperiksa kembali setelah dibuat.

# **14. ACCEPTANCE CRITERIA**

Dokumen dinyatakan memenuhi PRD apabila:

| ID    | Kriteria                                              |
| ----- | ----------------------------------------------------- |
| AC-01 | Output berupa DOCX editable                           |
| AC-02 | BAB I memiliki outline awal                           |
| AC-03 | BAB II memiliki outline awal                          |
| AC-04 | BAB III disusun lengkap                               |
| AC-05 | BAB IV disusun berdasarkan bukti aktual               |
| AC-06 | BAB V memiliki outline awal                           |
| AC-07 | Semua pengujian UAS tercantum                         |
| AC-08 | Seluruh metrik evaluasi dijelaskan                    |
| AC-09 | Variasi 1, 2, 4, 6, dan 9 Worker tercantum            |
| AC-10 | Konfigurasi node dan jaringan berdasarkan data aktual |
| AC-11 | Tidak terdapat angka eksperimen fiktif                |
| AC-12 | Semua screenshot dan tabel memiliki caption           |
| AC-13 | Dokumen memiliki heading styles dan daftar isi        |
| AC-14 | Referensi dapat diverifikasi                          |
| AC-15 | Dokumen berhasil dibuka dan diperiksa ulang           |

# **15. DEFINITION OF DONE**

Agent dianggap menyelesaikan tugas apabila:

- Seluruh sumber yang tersedia telah diinventarisasi.
- Dokumen UAS telah dianalisis.
- Skill DOCX yang relevan telah ditemukan dan digunakan.
- Repository dan konfigurasi telah diperiksa.
- BAB I telah memiliki outline.
- BAB II telah memiliki outline.
- BAB III telah disusun lengkap.
- BAB IV bagian implementasi telah disusun.
- BAB IV bagian pengukuran telah disiapkan dan diisi sesuai data.
- BAB IV bagian analisis telah disiapkan dan diisi sesuai data.
- BAB V telah memiliki outline.
- Semua placeholder telah ditandai.
- Semua data yang tersedia telah divalidasi.
- File DOCX berhasil dibuat.
- File DOCX berhasil dibuka kembali untuk QA.
- Daftar kekurangan dan data yang masih diperlukan telah disiapkan.

# **16. DAFTAR INPUT YANG PERLU DISEDIAKAN**

Jika belum ditemukan dalam repository atau lampiran, agent harus mengidentifikasi kebutuhan berikut.

| No. | Input                    | Kegunaan                      |
| --- | ------------------------ | ----------------------------- |
| 1   | Repository CrawlMesh     | Pemeriksaan implementasi      |
| 2   | README                   | Memahami sistem               |
| 3   | File konfigurasi         | Mengetahui konfigurasi aktual |
| 4   | Diagram topologi         | Dokumentasi arsitektur        |
| 5   | Inventaris 10 node fisik | Konfigurasi node              |
| 6   | Screenshot aplikasi      | Bukti implementasi            |
| 7   | Log Master dan Worker    | Validasi mekanisme            |
| 8   | CSV hasil benchmark      | Hasil pengukuran              |
| 9   | Data CPU dan RAM         | Evaluasi resource             |
| 10  | Log fault tolerance      | Analisis recovery             |
| 11  | Dokumentasi deployment   | Konfigurasi runtime           |
| 12  | Pedoman laporan kampus   | Penyesuaian format            |

# **17. INSTRUKSI FINAL UNTUK AI AGENT**

**PRIMARY EXECUTION DIRECTIVE**

Anda bertugas menyusun draft laporan proyek CrawlMesh berdasarkan PRD ini.

Prioritaskan penyelesaian BAB III dan sebagian BAB IV, tetapi tetap bangun struktur awal BAB I, BAB II, dan BAB V agar laporan dapat dikembangkan secara bertahap.

Lakukan inspeksi terhadap seluruh sumber yang tersedia sebelum menulis isi laporan. Gunakan semua skill DOCX yang relevan dan ikuti instruksi masing-masing skill.

Pastikan setiap pembahasan teknis berasal dari implementasi aktual, konfigurasi yang dapat diverifikasi, atau hasil eksperimen yang benar-benar tersedia.

Untuk informasi yang belum tersedia, gunakan placeholder yang jelas. Jangan membuat asumsi seolah-olah merupakan fakta.

Output akhir wajib berupa satu dokumen Microsoft Word `.docx` yang editable, memiliki struktur akademik, tabel, diagram, caption, daftar isi, dan format yang konsisten.

Setelah dokumen selesai, lakukan pemeriksaan ulang terhadap isi dan struktur file sebelum menyerahkannya.

## **18. STRATEGI PENGEMBANGAN LAPORAN SELANJUTNYA**

PRD ini dirancang agar pengerjaan laporan dapat dilakukan secara bertahap tanpa perlu membangun ulang struktur dokumen.

| Tahap               | Target                                                 | Hasil            |
| ------------------- | ------------------------------------------------------ | ---------------- |
| Tahap 1 — Sekarang | BAB III lengkap, BAB IV sebagian, outline BAB I, II, V | Draft laporan v1 |
| Tahap 2             | Pengembangan BAB I dan BAB II                          | Draft laporan v2 |
| Tahap 3             | Melengkapi data eksperimen dan BAB IV                  | Draft laporan v3 |
| Tahap 4             | Menyusun BAB V dan referensi final                     | Draft laporan v4 |
| Tahap 5             | Final proofreading, validasi sitasi, dan format        | Laporan final    |

**Prinsip utama:** Setiap tahap harus melanjutkan dokumen sebelumnya. Struktur heading, penomoran tabel, penomoran gambar, sitasi, dan konsistensi terminologi harus dipertahankan.

**Catatan penyusunan:** Struktur persyaratan UAS di atas mengacu pada dokumen *UJIAN AKHIR SEMESTER.pdf*, khususnya halaman 1–2. Outline BAB I, BAB II, dan BAB V merupakan usulan struktur pengembangan laporan, bukan ketentuan subbab yang secara eksplisit ditetapkan oleh dokumen UAS.&#x20;

UJIAN AKHIR SEMESTER.pdf
