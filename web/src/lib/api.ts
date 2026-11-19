import type {
  ClusterInfo,
  CrawlJob,
  DiscoverResponse,
  Experiment,
  HealthResponse,
  NodeInfo,
  Overview,
  ResultsPage,
  RunExperimentPayload,
  TaskRow,
} from "./types";

const BASE = "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* keep the HTTP status text */
    }
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  cluster: () => request<ClusterInfo | null>("/api/cluster"),
  initCluster: (name: string) =>
    request<ClusterInfo>("/api/cluster/init", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  overview: () => request<Overview>("/api/cluster/overview"),
  nodes: () => request<NodeInfo[]>("/api/nodes"),
  discover: () => request<DiscoverResponse>("/api/cluster/discover", { method: "POST" }),
  assignNode: (workerId: string) =>
    request<NodeInfo>(`/api/nodes/${encodeURIComponent(workerId)}/assign`, { method: "POST" }),
  removeNode: (workerId: string) =>
    request<NodeInfo>(`/api/nodes/${encodeURIComponent(workerId)}/remove`, { method: "POST" }),
  simulateFailure: (workerId: string) =>
    request<NodeInfo>(`/api/nodes/${encodeURIComponent(workerId)}/simulate-failure`, {
      method: "POST",
    }),
  recoverNode: (workerId: string) =>
    request<NodeInfo>(`/api/nodes/${encodeURIComponent(workerId)}/recover`, { method: "POST" }),
  addManual: (ip: string, port: number) =>
    request<NodeInfo>("/api/nodes/manual", {
      method: "POST",
      body: JSON.stringify({ ip_address: ip, port }),
    }),
  jobs: () => request<CrawlJob[]>("/api/jobs"),
  job: (jobId: string) => request<CrawlJob>(`/api/jobs/${jobId}`),
  createJob: (payload: Record<string, unknown>) =>
    request<CrawlJob>("/api/jobs", { method: "POST", body: JSON.stringify(payload) }),
  jobAction: (jobId: string, action: "pause" | "resume" | "cancel") =>
    request<CrawlJob>(`/api/jobs/${jobId}/${action}`, { method: "POST" }),
  tasks: (params: { jobId?: string; status?: string; worker?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.jobId) query.set("job_id", params.jobId);
    if (params.status) query.set("status", params.status);
    if (params.worker) query.set("worker", params.worker);
    query.set("limit", "200");
    return request<TaskRow[]>(`/api/tasks?${query.toString()}`);
  },
  results: (params: {
    jobId?: string;
    q?: string;
    status?: string;
    worker?: string;
    offset?: number;
    limit?: number;
  } = {}) => {
    const query = new URLSearchParams();
    if (params.jobId) query.set("job_id", params.jobId);
    if (params.q) query.set("q", params.q);
    if (params.status) query.set("status", params.status);
    if (params.worker) query.set("worker", params.worker);
    query.set("offset", String(params.offset ?? 0));
    query.set("limit", String(params.limit ?? 100));
    return request<ResultsPage>(`/api/results?${query.toString()}`);
  },
  exportUrl: (format: "csv" | "json", jobId?: string) => {
    const query = new URLSearchParams({ format });
    if (jobId) query.set("job_id", jobId);
    return `/api/results/export?${query.toString()}`;
  },
  experiments: (groupId?: string) => {
    const query = new URLSearchParams();
    if (groupId) query.set("group_id", groupId);
    return request<Experiment[]>(`/api/experiments?${query.toString()}`);
  },
  experiment: (experimentId: string, samples = false) =>
    request<Experiment>(
      `/api/experiments/${experimentId}?samples=${samples ? "true" : "false"}`,
    ),
  runExperiment: (payload: RunExperimentPayload) =>
    request<Experiment>("/api/experiments/run", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  cancelExperiment: (experimentId: string) =>
    request<Experiment>(`/api/experiments/${experimentId}/cancel`, { method: "POST" }),
  experimentExportUrl: (format: "csv" | "json") =>
    `/api/experiments/export?format=${format}`,
};
