import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ListChecks, RefreshCw, Timer } from "lucide-react";
import { api } from "../lib/api";
import { useCluster } from "../lib/cluster-context";
import { formatAgo, titleCase } from "../lib/format";
import type { TaskRow } from "../lib/types";
import { Panel, EmptyState } from "../components/Panel";
import { PhaseGate } from "../components/PhaseGate";
import { StatusPill } from "../components/StatusPill";

const TASK_TONE: Record<string, string> = {
  queued: "border-ink-600 bg-ink-800 text-mist-300",
  leased: "border-[#4a3716] bg-[#1d1608] text-[#fbd99a]",
  running: "border-[#4a3716] bg-[#1d1608] text-[#fbd99a]",
  completed: "border-[#3c5220] bg-[#141f0c] text-[#cdf98a]",
  failed: "border-[#4d2525] bg-[#1c0d0d] text-[#ffb3b3]",
  dead: "border-[#4d2525] bg-[#1c0d0d] text-[#ffb3b3]",
  cancelled: "border-ink-600 bg-ink-800 text-mist-400",
};

export function TasksPage() {
  const { overview } = useCluster();
  const [jobFilter, setJobFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const workers = (overview?.nodes ?? []).filter((node) => node.role === "worker");

  const jobsQuery = useQuery({ queryKey: ["jobs"], queryFn: api.jobs, refetchInterval: 5000 });
  const tasksQuery = useQuery({
    queryKey: ["tasks", jobFilter, statusFilter],
    queryFn: () => api.tasks({ jobId: jobFilter || undefined, status: statusFilter || undefined }),
    refetchInterval: 2000,
  });

  const tasks = tasksQuery.data ?? [];
  const jobs = jobsQuery.data ?? [];
  const jobName = (jobId: string) => jobs.find((job) => job.job_id === jobId)?.job_name ?? jobId;

  return (
    <div className="space-y-4">
      <Panel
        eyebrow="worker distribution"
        title="Per-worker state"
        actions={<span className="chip"><Timer className="size-3" /> live</span>}
        bodyClassName="p-0"
      >
        {workers.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px] text-left font-mono text-[0.7rem]">
              <thead>
                <tr className="border-b border-ink-800 text-[0.62rem] uppercase tracking-[0.14em] text-mist-500">
                  <th className="px-4 py-2.5 font-normal">worker</th>
                  <th className="px-4 py-2.5 font-normal">status</th>
                  <th className="px-4 py-2.5 text-right font-normal">inflight</th>
                  <th className="px-4 py-2.5 text-right font-normal">completed</th>
                  <th className="px-4 py-2.5 text-right font-normal">failed</th>
                  <th className="px-4 py-2.5 text-right font-normal">throughput</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-800">
                {workers.map((node) => (
                  <tr key={node.worker_id} className="hover:bg-ink-850/70">
                    <td className="px-4 py-2.5 text-mist-200">
                      {node.hostname}
                      <span className="ml-2 text-[0.6rem] text-mist-500">{node.ip_address}</span>
                    </td>
                    <td className="px-4 py-2.5">
                      <StatusPill status={node.status} />
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-mist-200">
                      {node.inflight}/{node.capacity}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-signal">
                      {node.completed_tasks}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-danger">
                      {node.failed_tasks}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-mist-300">
                      {node.throughput.toFixed(2)} p/s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-4">
            <EmptyState
              icon={<ListChecks className="size-6" />}
              title="Belum ada worker aktif"
              body="Distribusi task tampil per worker setelah minimal satu Worker di-assign."
            />
          </div>
        )}
      </Panel>

      <Panel
        eyebrow={`${tasks.length} task`}
        title="Task Ledger"
        actions={
          <>
            <select className="field !w-auto !py-1" value={jobFilter} onChange={(e) => setJobFilter(e.target.value)}>
              <option value="">all jobs</option>
              {jobs.map((job) => (
                <option key={job.job_id} value={job.job_id}>
                  {job.job_name}
                </option>
              ))}
            </select>
            <select
              className="field !w-auto !py-1"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">all status</option>
              {["queued", "leased", "running", "completed", "failed", "dead", "cancelled"].map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
            <button
              className="btn btn-ghost !px-2 !py-1"
              onClick={() => tasksQuery.refetch()}
              title="Refresh"
            >
              <RefreshCw className={`size-3.5 ${tasksQuery.isFetching ? "animate-spin" : ""}`} />
            </button>
          </>
        }
        bodyClassName="p-0"
      >
        {tasks.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-left font-mono text-[0.68rem]">
              <thead>
                <tr className="border-b border-ink-800 text-[0.6rem] uppercase tracking-[0.14em] text-mist-500">
                  <th className="px-4 py-2.5 font-normal">task</th>
                  <th className="px-4 py-2.5 font-normal">job</th>
                  <th className="px-4 py-2.5 font-normal">worker</th>
                  <th className="px-4 py-2.5 text-right font-normal">urls</th>
                  <th className="px-4 py-2.5 text-right font-normal">attempt</th>
                  <th className="px-4 py-2.5 font-normal">status</th>
                  <th className="px-4 py-2.5 font-normal">age</th>
                  <th className="px-4 py-2.5 font-normal">error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-800">
                {tasks.map((task) => (
                  <TaskTableRow key={task.task_id} task={task} jobName={jobName(task.job_id)} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-4">
            <EmptyState
              icon={<ListChecks className="size-6" />}
              title="Tidak ada task pada filter ini"
              body="Jalankan crawl job dari halaman Crawl Jobs; task akan muncul saat scheduler memecah frontier menjadi batch."
            />
          </div>
        )}
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <PhaseGate phase="phase 5" title="Failure console" acceptance="AC-10 · AC-11">
          Task yang kehilangan lease atau worker-nya offline akan otomatis requeue (attempt +1) dan
          dicatat di task events. Dead-letter muncul setelah 3 attempt.
        </PhaseGate>
        <Panel eyebrow="lease semantics" title="How tasks are assigned" bodyClassName="p-4">
          <ul className="space-y-1.5 font-mono text-[0.66rem] leading-relaxed text-mist-400">
            <li>• scheduler memecah frontier menjadi batch sesuai batch size</li>
            <li>• worker melakukan lease; master mereservasi kapasitas secara atomik</li>
            <li>• dynamic: task tanpa owner, diambil worker mana pun yang paling ringan</li>
            <li>• static: task dipre-assign round-robin saat dekomposisi</li>
            <li>• lease timeout = timeout × url_count + 60 s</li>
          </ul>
        </Panel>
      </div>
    </div>
  );
}

function TaskTableRow({ task, jobName }: { task: TaskRow; jobName: string }) {
  return (
    <tr className="hover:bg-ink-850/70">
      <td className="px-4 py-2.5 text-mist-200">{task.task_id}</td>
      <td className="px-4 py-2.5 text-mist-400">{jobName}</td>
      <td className="px-4 py-2.5 text-mist-400">{task.assigned_worker ?? "—"}</td>
      <td className="px-4 py-2.5 text-right tabular-nums text-mist-300">{task.url_count}</td>
      <td className="px-4 py-2.5 text-right tabular-nums text-mist-300">{task.attempt_count}</td>
      <td className="px-4 py-2.5">
        <span className={`chip ${TASK_TONE[task.status] ?? ""}`}>{titleCase(task.status)}</span>
      </td>
      <td className="px-4 py-2.5 text-mist-500">{formatAgo(task.created_at)}</td>
      <td className="max-w-[220px] truncate px-4 py-2.5 text-danger">{task.error ?? ""}</td>
    </tr>
  );
}
