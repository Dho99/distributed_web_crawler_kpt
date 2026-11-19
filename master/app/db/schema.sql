-- CrawlMesh master schema (SQLite, WAL).
-- All timestamps are ISO-8601 UTC strings.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cluster (
    id              INTEGER PRIMARY KEY CHECK (id = 1),
    cluster_id      TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    pairing_token   TEXT NOT NULL,
    master_url      TEXT NOT NULL,
    discovery_port  INTEGER NOT NULL DEFAULT 5599,
    sampling_ms     INTEGER NOT NULL DEFAULT 2000,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nodes (
    worker_id        TEXT PRIMARY KEY,
    hostname         TEXT NOT NULL,
    ip_address       TEXT NOT NULL DEFAULT '',
    port             INTEGER NOT NULL DEFAULT 8010,
    role             TEXT NOT NULL DEFAULT 'worker',
    status           TEXT NOT NULL DEFAULT 'pending',
    cpu_cores        INTEGER NOT NULL DEFAULT 1,
    memory_total     INTEGER NOT NULL DEFAULT 0,
    os_name          TEXT NOT NULL DEFAULT '',
    python_version   TEXT NOT NULL DEFAULT '',
    agent_version    TEXT NOT NULL DEFAULT '',
    pool_size        INTEGER NOT NULL DEFAULT 1,
    capacity         INTEGER NOT NULL DEFAULT 1,
    last_heartbeat   TEXT,
    registered_at    TEXT,
    removed_at       TEXT,
    simulated_offline INTEGER NOT NULL DEFAULT 0,
    -- latest resource sample, denormalised for fast dashboard reads
    cpu_usage        REAL NOT NULL DEFAULT 0,
    memory_usage     REAL NOT NULL DEFAULT 0,
    active_tasks     INTEGER NOT NULL DEFAULT 0,
    completed_tasks  INTEGER NOT NULL DEFAULT 0,
    failed_tasks     INTEGER NOT NULL DEFAULT 0,
    child_processes  INTEGER NOT NULL DEFAULT 0,
    inflight         INTEGER NOT NULL DEFAULT 0,
    throughput       REAL NOT NULL DEFAULT 0,
    meta             TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);

CREATE TABLE IF NOT EXISTS jobs (
    job_id           TEXT PRIMARY KEY,
    job_name         TEXT NOT NULL,
    seed_urls        TEXT NOT NULL,
    allowed_domains  TEXT NOT NULL,
    maximum_pages    INTEGER NOT NULL,
    maximum_depth    INTEGER NOT NULL,
    batch_size       INTEGER NOT NULL,
    request_timeout  REAL NOT NULL,
    domain_delay     REAL NOT NULL,
    respect_robots   INTEGER NOT NULL DEFAULT 1,
    user_agent       TEXT NOT NULL DEFAULT '',
    worker_allowlist TEXT NOT NULL DEFAULT '[]',
    scheduling_mode  TEXT NOT NULL DEFAULT 'dynamic',
    include_subdomains INTEGER NOT NULL DEFAULT 0,
    allow_private_targets INTEGER NOT NULL DEFAULT 0,
    status           TEXT NOT NULL DEFAULT 'pending',
    workload_key     TEXT NOT NULL DEFAULT '',
    config_hash      TEXT NOT NULL DEFAULT '',
    created_at       TEXT NOT NULL,
    started_at       TEXT,
    completed_at     TEXT,
    pages_crawled    INTEGER NOT NULL DEFAULT 0,
    pages_failed     INTEGER NOT NULL DEFAULT 0,
    throughput       REAL NOT NULL DEFAULT 0,
    -- experiment linkage
    experiment_id    TEXT,
    mode             TEXT NOT NULL DEFAULT 'distributed'
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

CREATE TABLE IF NOT EXISTS frontier_urls (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id        TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    url           TEXT NOT NULL,
    url_hash      TEXT NOT NULL,
    domain        TEXT NOT NULL DEFAULT '',
    depth         INTEGER NOT NULL DEFAULT 0,
    priority      INTEGER NOT NULL DEFAULT 0,
    state         TEXT NOT NULL DEFAULT 'queued',
    discovered_at TEXT NOT NULL,
    enqueued_at   TEXT,
    scheduled_at  TEXT,
    finished_at   TEXT,
    UNIQUE (job_id, url_hash)
);

CREATE INDEX IF NOT EXISTS idx_frontier_job_state ON frontier_urls(job_id, state, priority DESC, id);
CREATE INDEX IF NOT EXISTS idx_frontier_job_domain ON frontier_urls(job_id, domain);

CREATE TABLE IF NOT EXISTS tasks (
    task_id         TEXT PRIMARY KEY,
    job_id          TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    depth           INTEGER NOT NULL DEFAULT 0,
    urls            TEXT NOT NULL,
    url_count       INTEGER NOT NULL DEFAULT 0,
    priority        INTEGER NOT NULL DEFAULT 0,
    assigned_worker TEXT,
    attempt_count   INTEGER NOT NULL DEFAULT 0,
    max_attempts    INTEGER NOT NULL DEFAULT 3,
    status          TEXT NOT NULL DEFAULT 'queued',
    created_at      TEXT NOT NULL,
    leased_at       TEXT,
    lease_deadline  TEXT,
    completed_at    TEXT,
    failed_at       TEXT,
    error           TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_job_status ON tasks(job_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_worker ON tasks(assigned_worker, status);

CREATE TABLE IF NOT EXISTS results (
    result_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id          TEXT NOT NULL,
    job_id           TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    url              TEXT NOT NULL,
    url_hash         TEXT NOT NULL,
    final_url        TEXT NOT NULL DEFAULT '',
    title            TEXT NOT NULL DEFAULT '',
    extracted_text   TEXT NOT NULL DEFAULT '',
    http_status      INTEGER NOT NULL DEFAULT 0,
    content_hash     TEXT NOT NULL DEFAULT '',
    response_time_ms REAL NOT NULL DEFAULT 0,
    size_bytes       INTEGER NOT NULL DEFAULT 0,
    links_found      INTEGER NOT NULL DEFAULT 0,
    worker_id        TEXT NOT NULL DEFAULT '',
    crawled_at       TEXT NOT NULL,
    error            TEXT,
    UNIQUE (job_id, url_hash)
);

CREATE INDEX IF NOT EXISTS idx_results_job_status ON results(job_id, http_status);
CREATE INDEX IF NOT EXISTS idx_results_job_time ON results(job_id, response_time_ms);
CREATE INDEX IF NOT EXISTS idx_results_worker ON results(worker_id);

CREATE TABLE IF NOT EXISTS worker_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id       TEXT NOT NULL,
    cpu_usage       REAL NOT NULL DEFAULT 0,
    memory_usage    REAL NOT NULL DEFAULT 0,
    active_processes INTEGER NOT NULL DEFAULT 0,
    child_processes INTEGER NOT NULL DEFAULT 0,
    active_tasks    INTEGER NOT NULL DEFAULT 0,
    throughput      REAL NOT NULL DEFAULT 0,
    recorded_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_metrics_worker_time ON worker_metrics(worker_id, recorded_at);

CREATE TABLE IF NOT EXISTS task_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL,
    job_id      TEXT NOT NULL,
    worker_id   TEXT,
    event       TEXT NOT NULL,
    detail      TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_task_events_task ON task_events(task_id, created_at);
CREATE INDEX IF NOT EXISTS idx_task_events_job ON task_events(job_id, created_at);

CREATE TABLE IF NOT EXISTS failure_events (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id         TEXT NOT NULL,
    detected_at       TEXT NOT NULL,
    affected_tasks    INTEGER NOT NULL DEFAULT 0,
    requeued_tasks    INTEGER NOT NULL DEFAULT 0,
    replacement_worker TEXT,
    recovered_at      TEXT,
    recovery_time_ms  REAL,
    detail            TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id     TEXT PRIMARY KEY,
    experiment_type   TEXT NOT NULL,
    worker_count      INTEGER NOT NULL DEFAULT 0,
    workload_key      TEXT NOT NULL DEFAULT '',
    scheduling_mode   TEXT NOT NULL DEFAULT 'dynamic',
    status            TEXT NOT NULL DEFAULT 'completed',
    group_id          TEXT,
    progress_pages    INTEGER NOT NULL DEFAULT 0,
    total_pages       INTEGER NOT NULL DEFAULT 0,
    execution_time_ms REAL NOT NULL DEFAULT 0,
    pages_ok          INTEGER NOT NULL DEFAULT 0,
    pages_failed      INTEGER NOT NULL DEFAULT 0,
    speedup           REAL,
    efficiency        REAL,
    throughput        REAL NOT NULL DEFAULT 0,
    cpu_utilization   REAL NOT NULL DEFAULT 0,
    memory_utilization REAL NOT NULL DEFAULT 0,
    recovery_time_ms  REAL,
    baseline_id       TEXT,
    config            TEXT NOT NULL DEFAULT '{}',
    notes             TEXT NOT NULL DEFAULT '',
    error             TEXT,
    created_at        TEXT NOT NULL,
    finished_at       TEXT
);

CREATE INDEX IF NOT EXISTS idx_experiments_type ON experiments(experiment_type, created_at);

CREATE TABLE IF NOT EXISTS experiment_samples (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    ts_offset_ms  INTEGER NOT NULL,
    cpu_usage     REAL NOT NULL DEFAULT 0,
    memory_usage  REAL NOT NULL DEFAULT 0,
    pages_done    INTEGER NOT NULL DEFAULT 0,
    throughput    REAL NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_exp_samples ON experiment_samples(experiment_id, ts_offset_ms);

CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT NOT NULL,
    message    TEXT NOT NULL,
    payload    TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_time ON events(created_at);
