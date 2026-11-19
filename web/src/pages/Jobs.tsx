import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  Ban,
  CheckCircle2,
  Gauge,
  Loader2,
  Pause,
  Play,
  Plus,
  ShieldCheck,
  Timer,
} from "lucide-react";
import { api } from "../lib/api";
import { useCluster } from "../lib/cluster-context";
import { titleCase } from "../lib/format";
import type { CrawlJob, JobStatus } from "../lib/types";
import { Panel, EmptyState } from "../components/Panel";
import { PhaseGate } from "../components/PhaseGate";

const DEFAULTS = {
  jobName: "Bench Crawl",
  seedUrl: "http://127.0.0.1:8000/bench/",
  maxPages: "100",
  maxDepth: "1",
  batchSize: "5",
  timeout: "10",
  delay: "0.05",
  scheduling: "dynamic" as "dynamic" | "static",
  robots: true,
};

const JOB_TONE: Record<JobStatus, string> = {
  pending: "border-ink-600 bg-ink-800 text-mist-300",
  running: "border-[#3c5220] bg-[#141f0c] text-[#cdf98a]",
  paused: "border-[#4a3716] bg-[#1d1608] text-[#fbd99a]",
  completed: "border-[#1d4450] bg-[#0b1a1f] text-[#a9eef5]",
  failed: "border-[#4d2525] bg-[#1c0d0d] text-[#ffb3b3]",
  cancelled: "border-ink-600 bg-ink-800 text-mist-400",
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return (
    <span className={`chip ${JOB_TONE[status]}`}>{titleCase(status)}</span>
  );
}

export function JobsPage() {
  const { overview } = useCluster();
  const queryClient = useQueryClient();
  const [form, setForm] = useState(DEFAULTS);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: api.jobs,
    refetchInterval: 3000,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["jobs"] });
    queryClient.invalidateQueries({ queryKey: ["overview"] });
  };

  const createMutation = useMutation({
    mutationFn: () =>
      api.createJob({
        job_name: form.jobName.trim(),
        seed_urls: [form.seedUrl.trim()],
        maximum_pages: Number(form.maxPages) || 100,
        maximum_depth: Number(form.maxDepth) || 0,
        batch_size: Number(form.batchSize) || 10,
        request_timeout: Number(form.timeout) || 15,
        domain_delay: Number(form.delay) || 0,
        respect_robots: form.robots,
        scheduling_mode: form.scheduling,
      }),
    onSuccess: (job) => {
      setError(null);
      setNotice(`Job ${job.job_name} dimulai (${job.job_id}).`);
      invalidate();
    },
    onError: (err) => setError((err as Error).message),
  });

  const actionMutation = useMutation({
    mutationFn: ({ jobId, action }: { jobId: string; action: "pause" | "resume" | "cancel" }) =>
      api.jobAction(jobId, action),
    onSettled: invalidate,
  });

  const update = <K extends keyof typeof DEFAULTS>(key: K, value: (typeof DEFAULTS)[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const jobs = jobsQuery.data ?? [];
  const activeWorkers = overview?.active_workers ?? 0;

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.seedUrl.trim() || !form.jobName.trim()) return;
    createMutation.mutate();
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Panel
          eyebrow="new workload"
          title="Create Crawl Job"
          actions={<span className="chip"><Plus className="size-3" /> live engine</span>}
          bodyClassName="p-4"
        >
          <form className="space-y-3.5" onSubmit={submit}>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="job name">
                <input className="field" value={form.jobName} onChange={(e) => update("jobName", e.target.value)} />
              </Field>
              <Field label="seed url">
                <input className="field" value={form.seedUrl} onChange={(e) => update("seedUrl", e.target.value)} />
              </Field>
              <Field label="maximum pages">
                <input className="field" value={form.maxPages} onChange={(e) => update("maxPages", e.target.value)} />
              </Field>
              <Field label="maximum depth">
                <input className="field" value={form.maxDepth} onChange={(e) => update("maxDepth", e.target.value)} />
              </Field>
              <Field label="batch size">
                <input className="field" value={form.batchSize} onChange={(e) => update("batchSize", e.target.value)} />
              </Field>
              <Field label="request timeout (s)">
                <input className="field" value={form.timeout} onChange={(e) => update("timeout", e.target.value)} />
              </Field>
              <Field label="domain delay (s)">
                <input className="field" value={form.delay} onChange={(e) => update("delay", e.target.value)} />
              </Field>
              <Field label="scheduling">
                <select
                  className="field"
                  value={form.scheduling}
                  onChange={(e) => update("scheduling", e.target.value as "dynamic" | "static")}
                >
                  <option value="dynamic">Dynamic load balancing</option>
                  <option value="static">Static round-robin</option>
                </select>
              </Field>
            </div>

            <label className="flex items-center gap-2 font-mono text-[0.7rem] text-mist-400">
              <input
                type="checkbox"
                checked={form.robots}
                onChange={(e) => update("robots", e.target.checked)}
                className="size-3.5 accent-[#b8f24a]"
              />
              respect robots.txt &amp; per-domain delay
            </label>

            <div className="flex flex-wrap items-center gap-2 border-t border-ink-800 pt-3">
              <button className="btn btn-primary" type="submit" disabled={createMutation.isPending || !activeWorkers}>
                {createMutation.isPending ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
                {createMutation.isPending ? "starting…" : "start crawling"}
              </button>
              {!activeWorkers ? (
                <span className="font-mono text-[0.64rem] text-amber">
                  butuh minimal 1 worker aktif
                </span>
              ) : (
                <span className="font-mono text-[0.64rem] text-mist-500">
                  {activeWorkers} worker siap menerima lease
                </span>
              )}
            </div>

            {error ? (
              <div className="rounded border border-[#4d2525] bg-[#1c0d0d] px-3 py-2 font-mono text-[0.66rem] text-[#ffb3b3]">
                {error}
              </div>
            ) : null}
            {notice ? (
              <div className="rounded border border-[#3c5220] bg-[#0f1709] px-3 py-2 font-mono text-[0.66rem] text-[#cdf98a]">
                {notice}
              </div>
            ) : null}
          </form>
        </Panel>

        <div className="flex flex-col gap-4">
          <Panel eyebrow="cluster readiness" title="Pre-flight checks" bodyClassName="p-4">
            <ul className="space-y-2 font-mono text-[0.7rem]">
              <CheckRow ok={Boolean(overview?.cluster)} label="master initialised" />
              <CheckRow ok={activeWorkers > 0} label="≥1 active worker" />
              <CheckRow ok={activeWorkers >= 9} label="9 workers enrolled (target UAS)" />
              <CheckRow ok={Boolean(overview?.cluster)} label="crawl engine wired" />
            </ul>
          </Panel>

          <Panel eyebrow="parameter contract" title="Job configuration" bodyClassName="p-4">
            <pre className="overflow-x-auto rounded border border-ink-700 bg-ink-900 p-3 font-mono text-[0.64rem] leading-relaxed text-mist-400">
{`Job Name       : ${form.jobName}
Seed URL       : ${form.seedUrl}
Maximum Pages  : ${form.maxPages}
Maximum Depth  : ${form.maxDepth}
Batch Size     : ${form.batchSize}
Timeout        : ${form.timeout} s
Domain Delay   : ${form.delay} s
Scheduling     : ${form.scheduling}
Robots.txt     : ${form.robots ? "Enabled" : "Disabled"}`}
            </pre>
          </Panel>

          <PhaseGate phase="phase 3+" title="Multiprocessing & benchmark" acceptance="AC-07 · AC-14">
            Task saat ini dieksekusi pool multiprocessing di setiap worker. Phase 6 menambahkan runner
            benchmark otomatis dan penyimpanan speedup/efficiency.
          </PhaseGate>
        </div>
      </div>

      <Panel
        eyebrow={`${jobs.length} total`}
        title="Crawl Jobs"
        actions={<span className="chip"><Timer className="size-3" /> 3s refresh</span>}
        bodyClassName="p-0"
      >
        {jobs.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left font-mono text-[0.7rem]">
              <thead>
                <tr className="border-b border-ink-800 text-[0.6rem] uppercase tracking-[0.14em] text-mist-500">
                  <th className="px-4 py-2.5 font-normal">job</th>
                  <th className="px-4 py-2.5 font-normal">status</th>
                  <th className="px-4 py-2.5 font-normal">pages</th>
                  <th className="px-4 py-2.5 text-right font-normal">pending</th>
                  <th className="px-4 py-2.5 text-right font-normal">tasks</th>
                  <th className="px-4 py-2.5 text-right font-normal">throughput</th>
                  <th className="px-4 py-2.5 text-right font-normal">actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-800">
                {jobs.map((job) => (
                  <JobRow
                    key={job.job_id}
                    job={job}
                    busy={actionMutation.isPending}
                    onAction={(action) => actionMutation.mutate({ jobId: job.job_id, action })}
                  />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-4">
            <EmptyState
              icon={<Gauge className="size-6" />}
              title="Belum ada crawl job"
              body="Isi form di atas dan tekan START CRAWLING. Job akan langsung masuk ke scheduler dan di-lease oleh worker aktif."
            />
          </div>
        )}
      </Panel>
    </div>
  );
}

function JobRow({
  job,
  busy,
  onAction,
}: {
  job: CrawlJob;
  busy: boolean;
  onAction: (action: "pause" | "resume" | "cancel") => void;
}) {
  const progress = Math.min(100, (job.pages_crawled / Math.max(1, job.maximum_pages)) * 100);
  const finished = ["completed", "cancelled", "failed"].includes(job.status);

  return (
    <tr className="align-top hover:bg-ink-850/60">
      <td className="px-4 py-3">
        <div className="text-mist-100">{job.job_name}</div>
        <div className="mt-0.5 max-w-[280px] truncate text-[0.62rem] text-mist-500">
          {job.seed_urls[0]}
        </div>
        <div className="text-[0.58rem] text-mist-500/70">{job.job_id}</div>
      </td>
      <td className="px-4 py-3">
        <JobStatusBadge status={job.status} />
        <div className="mt-1 text-[0.6rem] text-mist-500">{job.scheduling_mode}</div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-baseline gap-1.5">
          <span className="text-mist-100">{job.pages_crawled}</span>
          <span className="text-[0.6rem] text-mist-500">/ {job.maximum_pages}</span>
          {job.pages_failed ? <span className="text-[0.6rem] text-danger">({job.pages_failed} fail)</span> : null}
        </div>
        <div className="mt-1.5 h-1 w-32 rounded bg-ink-700">
          <div
            className={finished ? "h-1 rounded bg-ice" : "h-1 rounded bg-signal"}
            style={{ width: `${progress}%` }}
          />
        </div>
      </td>
      <td className="px-4 py-3 text-right tabular-nums text-mist-300">{job.pages_pending}</td>
      <td className="px-4 py-3 text-right tabular-nums text-mist-300">
        {job.tasks_completed}/{job.tasks_total}
        {job.tasks_failed ? <span className="ml-1 text-danger">· {job.tasks_failed} fail</span> : null}
      </td>
      <td className="px-4 py-3 text-right tabular-nums text-mist-300">
        {job.throughput.toFixed(2)} p/s
      </td>
      <td className="px-4 py-3">
        <div className="flex justify-end gap-1.5">
          {job.status === "running" ? (
            <button className="btn !px-2 !py-1" title="Pause" disabled={busy} onClick={() => onAction("pause")}>
              <Pause className="size-3.5" />
            </button>
          ) : null}
          {job.status === "paused" ? (
            <button className="btn !px-2 !py-1" title="Resume" disabled={busy} onClick={() => onAction("resume")}>
              <Play className="size-3.5" />
            </button>
          ) : null}
          {job.status === "running" || job.status === "paused" ? (
            <button className="btn !px-2 !py-1" title="Cancel" disabled={busy} onClick={() => onAction("cancel")}>
              <Ban className="size-3.5 text-danger" />
            </button>
          ) : null}
          {job.status === "completed" ? (
            <span className="chip border-[#1d4450] bg-[#0b1a1f] text-[#a9eef5]">
              <CheckCircle2 className="size-3" /> done
            </span>
          ) : null}
        </div>
      </td>
    </tr>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="eyebrow">{label}</span>
      {children}
    </label>
  );
}

function CheckRow({ ok, label }: { ok: boolean; label: string }) {
  return (
    <li className="flex items-center justify-between gap-3">
      <span className="text-mist-400">{label}</span>
      <span className={ok ? "text-signal" : "text-mist-500"}>
        {ok ? <ShieldCheck className="size-3.5" /> : "pending"}
      </span>
    </li>
  );
}
