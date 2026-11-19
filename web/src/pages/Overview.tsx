import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  ArrowUpRight,
  Boxes,
  Cpu,
  FileSearch,
  Gauge,
  Network,
  Radar,
  ServerCog,
  Waypoints,
} from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useCluster } from "../lib/cluster-context";
import { formatClock, titleCase } from "../lib/format";
import type { LiveEvent } from "../lib/types";
import { NodeCard } from "../components/NodeCard";
import { Panel } from "../components/Panel";
import { StatTile } from "../components/StatTile";

const FEED_TONE: Record<string, string> = {
  "cluster.initialized": "text-signal",
  "node.updated": "text-ice",
  "node.offline": "text-danger",
  "node.removed": "text-amber",
  "failure.simulated": "text-amber",
};

function describe(event: LiveEvent): string {
  const payload = event.payload as Record<string, unknown> | null;
  switch (event.kind) {
    case "cluster.initialized":
      return `Cluster ${String(payload?.cluster_id ?? "")} initialised`;
    case "node.updated":
      return `${String(payload?.hostname ?? "node")} → ${titleCase(String(payload?.status ?? ""))}`;
    case "node.offline":
      return `${String(payload?.worker_id ?? "worker")} heartbeat lost`;
    case "node.removed":
      return `${String(payload?.worker_id ?? "worker")} removed from cluster`;
    case "failure.simulated":
      return `Failure simulated on ${String(payload?.worker_id ?? "worker")}`;
    case "job.updated":
      return `Job ${String(payload?.job_name ?? "")} → ${titleCase(String(payload?.status ?? ""))}`;
    case "job.completed":
      return `Job ${String(payload?.job_name ?? "")} completed · ${String(payload?.pages_crawled ?? 0)} pages`;
    case "task.completed":
      return `Task ${String(payload?.task_id ?? "")} completed`;
    case "task.requeued":
      return `Task ${String(payload?.task_id ?? "")} requeued (${String(payload?.status ?? "")})`;
    case "task.failed":
      return `Task ${String(payload?.task_id ?? "")} failed`;
    case "worker.failed":
      return `Worker ${String(payload?.worker_id ?? "")} failed · ${String(payload?.affected_tasks ?? 0)} tasks requeued`;
    case "experiment.updated":
      return `Experiment ${String(payload?.experiment_type ?? "")} → ${titleCase(String(payload?.status ?? ""))}`;
    default:
      return event.kind;
  }
}

function ActivityFeed({ feed }: { feed: LiveEvent[] }) {
  if (!feed.length) {
    return (
      <div className="rounded-lg border border-dashed border-ink-700 px-4 py-6 text-center font-mono text-[0.68rem] text-mist-500">
        waiting for cluster events…
      </div>
    );
  }
  return (
    <ol className="space-y-0 divide-y divide-ink-800">
      {feed.slice(0, 12).map((event, index) => (
        <li key={`${event.ts}-${index}`} className="flex items-start gap-2.5 py-2">
          <span className="mt-1 font-mono text-[0.6rem] tabular-nums text-mist-500">
            {formatClock(event.ts)}
          </span>
          <span className={`mt-0.5 size-1.5 shrink-0 rounded-full bg-current ${FEED_TONE[event.kind] ?? "text-mist-500"}`} />
          <span className="min-w-0 flex-1 font-mono text-[0.68rem] leading-relaxed text-mist-300">
            {describe(event)}
          </span>
        </li>
      ))}
    </ol>
  );
}

export function OverviewPage() {
  const { overview, feed, connected } = useCluster();
  const queryClient = useQueryClient();

  const initMutation = useMutation({
    mutationFn: () => api.initCluster("CrawlMesh Lab"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["overview"] }),
  });

  if (!overview?.cluster) {
    return (
      <div className="mx-auto max-w-2xl pt-10">
        <Panel eyebrow="bootstrap" title="Master belum diinisialisasi">
          <p className="text-[0.82rem] leading-relaxed text-mist-400">
            Inisialisasi node ini sebagai Master. Sistem akan membuat Cluster ID, pairing token, dan
            endpoint komunikasi untuk Worker Agent. Hanya satu Master yang diizinkan per cluster.
          </p>
          <div className="mt-4 flex items-center gap-3">
            <button
              className="btn btn-primary"
              onClick={() => initMutation.mutate()}
              disabled={initMutation.isPending}
            >
              <ServerCog className="size-3.5" />
              {initMutation.isPending ? "initialising…" : "Initialize this node as master"}
            </button>
            <span className="font-mono text-[0.65rem] text-mist-500">
              stream {connected ? "connected" : "disconnected"}
            </span>
          </div>
          {initMutation.error ? (
            <div className="mt-3 rounded border border-[#4d2525] bg-[#1c0d0d] px-3 py-2 font-mono text-[0.68rem] text-[#ffb3b3]">
              {String((initMutation.error as Error).message)}
            </div>
          ) : null}
        </Panel>
      </div>
    );
  }

  const nodes = overview.nodes;
  const workers = nodes.filter((node) => node.role === "worker");
  const master = nodes.find((node) => node.role === "master") ?? null;
  const enrolled = workers.filter((n) => !["pending", "removed", "discovered"].includes(n.status));
  const poolTotal = nodes.reduce((sum, node) => sum + node.pool_size, 0);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <StatTile
          label="Active workers"
          value={`${overview.active_workers}`}
          hint={`target 9 · ${workers.length} enrolled`}
          icon={<Network className="size-4" />}
          tone="signal"
        />
        <StatTile
          label="Total nodes"
          value={`${overview.total_nodes}`}
          hint={`${overview.offline_workers} offline`}
          icon={<Waypoints className="size-4" />}
        />
        <StatTile
          label="CPU cores"
          value={overview.total_cpu_cores}
          hint={`${poolTotal} pool processes`}
          icon={<Cpu className="size-4" />}
          tone="ice"
        />
        <StatTile
          label="Pages crawled"
          value={overview.pages_crawled}
          hint="aggregated results"
          icon={<FileSearch className="size-4" />}
        />
        <StatTile
          label="Throughput"
          value={`${overview.current_throughput.toFixed(2)}`}
          hint="pages / second (10s window)"
          icon={<Gauge className="size-4" />}
          tone="amber"
        />
        <StatTile
          label="Running jobs"
          value={overview.running_jobs}
          hint={`${overview.failed_tasks} failed tasks`}
          icon={<Boxes className="size-4" />}
          tone={overview.failed_tasks > 0 ? "danger" : "default"}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.65fr)_minmax(0,1fr)]">
        <Panel
          eyebrow={`${enrolled.length}/9 workers enrolled`}
          title="Cluster members"
          actions={
            <Link to="/discovery" className="btn btn-ghost">
              <Radar className="size-3.5" /> discover
            </Link>
          }
          bodyClassName="p-3"
        >
          <div className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-3">
            {master ? <NodeCard node={master} /> : null}
            {workers.map((node) => (
              <NodeCard key={node.worker_id} node={node} />
            ))}
          </div>
          {!workers.length ? (
            <div className="mt-3 rounded-lg border border-dashed border-ink-700 px-4 py-6 text-center">
              <p className="font-mono text-[0.7rem] text-mist-500">
                Belum ada Worker terdaftar. Jalankan agent di komputer lain, lalu lakukan scan.
              </p>
              <Link to="/discovery" className="btn mt-3">
                <Radar className="size-3.5" /> open discovery
              </Link>
            </div>
          ) : null}
        </Panel>

        <div className="flex min-w-0 flex-col gap-4">
          <Panel
            eyebrow="realtime"
            title="Activity"
            actions={
              <span className="chip">
                <Activity className="size-3" /> {feed.length}
              </span>
            }
            bodyClassName="px-4 py-2"
          >
            <ActivityFeed feed={feed} />
          </Panel>

          <Panel eyebrow="capacity" title="Processing capacity" bodyClassName="p-4">
            <dl className="space-y-2 font-mono text-[0.7rem]">
              <div className="flex items-baseline justify-between">
                <dt className="text-mist-500">pool processes</dt>
                <dd className="text-mist-100">{poolTotal}</dd>
              </div>
              <div className="flex items-baseline justify-between">
                <dt className="text-mist-500">inflight tasks</dt>
                <dd className="text-mist-100">
                  {nodes.reduce((sum, node) => sum + node.inflight, 0)}
                </dd>
              </div>
              <div className="flex items-baseline justify-between">
                <dt className="text-mist-500">worker throughput</dt>
                <dd className="text-signal">
                  {workers.reduce((sum, node) => sum + node.throughput, 0).toFixed(2)} p/s
                </dd>
              </div>
              <div className="flex items-baseline justify-between border-t border-ink-800 pt-2">
                <dt className="text-mist-500">cluster id</dt>
                <dd className="text-mist-300">{overview.cluster.cluster_id}</dd>
              </div>
            </dl>
            <Link
              to="/topology"
              className="mt-3 inline-flex items-center gap-1 font-mono text-[0.66rem] text-ice hover:text-signal"
            >
              inspect topology <ArrowUpRight className="size-3" />
            </Link>
          </Panel>
        </div>
      </div>
    </div>
  );
}
