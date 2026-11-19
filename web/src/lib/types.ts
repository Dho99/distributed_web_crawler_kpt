export type NodeRole = "master" | "worker";

export type NodeStatus =
  | "discovered"
  | "pending"
  | "online"
  | "busy"
  | "idle"
  | "degraded"
  | "offline"
  | "removed";

export interface NodeInfo {
  worker_id: string;
  hostname: string;
  ip_address: string;
  port: number;
  role: NodeRole;
  status: NodeStatus;
  cpu_cores: number;
  memory_total: number;
  os_name: string;
  python_version: string;
  pool_size: number;
  agent_version: string;
  last_heartbeat: string | null;
  registered_at: string | null;
  cpu_usage: number;
  memory_usage: number;
  active_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  child_processes: number;
  inflight: number;
  capacity: number;
  throughput: number;
}

export interface ClusterInfo {
  cluster_id: string;
  name: string;
  pairing_token: string;
  master_url: string;
  created_at: string;
  discovery_port: number;
}

export interface Overview {
  cluster: ClusterInfo | null;
  total_nodes: number;
  active_workers: number;
  offline_workers: number;
  total_cpu_cores: number;
  total_memory: number;
  running_jobs: number;
  pages_crawled: number;
  failed_tasks: number;
  current_throughput: number;
  nodes: NodeInfo[];
}

export interface DiscoveredNode {
  worker_id: string;
  hostname: string;
  ip_address: string;
  port: number;
  cpu_cores: number;
  memory_total: number;
  os_name: string;
  python_version: string;
  agent_version: string;
  cluster_id: string | null;
  reachable: boolean;
  already_known: boolean;
}

export interface DiscoverResponse {
  found: DiscoveredNode[];
  scanned_ms: number;
  already_known: string[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  cluster_id: string | null;
  initialized: boolean;
  db: string;
}

export interface LiveEvent {
  kind: string;
  ts: string;
  payload: unknown;
}

export type JobStatus =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export interface CrawlJob {
  job_id: string;
  job_name: string;
  seed_urls: string[];
  allowed_domains: string[];
  maximum_pages: number;
  maximum_depth: number;
  batch_size: number;
  request_timeout: number;
  domain_delay: number;
  respect_robots: boolean;
  scheduling_mode: "static" | "dynamic";
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  pages_crawled: number;
  pages_failed: number;
  pages_pending: number;
  tasks_total: number;
  tasks_completed: number;
  tasks_failed: number;
  throughput: number;
}

export interface TaskRow {
  task_id: string;
  job_id: string;
  depth: number;
  url_count: number;
  assigned_worker: string | null;
  attempt_count: number;
  status: string;
  created_at: string;
  leased_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface ResultRow {
  result_id: number;
  job_id: string;
  url: string;
  title: string;
  http_status: number;
  response_time_ms: number;
  links_found: number;
  size_bytes: number;
  content_hash: string;
  worker_id: string;
  crawled_at: string;
  error: string | null;
}

export interface ResultsPage {
  total: number;
  items: ResultRow[];
}

export type ExperimentType =
  | "sequential"
  | "local_parallel"
  | "distributed"
  | "scalability"
  | "load_balancing"
  | "fault_tolerance";

export interface ExperimentSample {
  ts_offset_ms: number;
  cpu_usage: number;
  memory_usage: number;
  pages_done: number;
}

export interface Experiment {
  experiment_id: string;
  experiment_type: ExperimentType;
  worker_count: number;
  workload_key: string;
  scheduling_mode: "static" | "dynamic";
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  group_id: string | null;
  progress_pages: number;
  total_pages: number;
  execution_time_ms: number;
  pages_ok: number;
  pages_failed: number;
  speedup: number | null;
  efficiency: number | null;
  throughput: number;
  cpu_utilization: number;
  memory_utilization: number;
  recovery_time_ms: number | null;
  baseline_id: string | null;
  config: Record<string, unknown>;
  notes: string;
  error: string | null;
  created_at: string;
  finished_at: string | null;
  samples?: ExperimentSample[];
}

export interface RunExperimentPayload {
  experiment_type: ExperimentType;
  worker_count?: number;
  maximum_pages?: number;
  maximum_depth?: number;
  batch_size?: number;
  domain_delay?: number;
  scheduling_mode?: "static" | "dynamic";
  repeat?: number;
}

export const STATUS_LABEL: Record<NodeStatus, string> = {
  discovered: "Discovered",
  pending: "Pending",
  online: "Online",
  busy: "Busy",
  idle: "Idle",
  degraded: "Degraded",
  offline: "Offline",
  removed: "Removed",
};
