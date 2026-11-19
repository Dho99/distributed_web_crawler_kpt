import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  Activity,
  Ban,
  FlaskConical,
  Gauge,
  Loader2,
  Play,
  TrendingUp,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../lib/api";
import { useCluster } from "../lib/cluster-context";
import { titleCase } from "../lib/format";
import type { Experiment, ExperimentType } from "../lib/types";
import { Panel } from "../components/Panel";
import { StatTile } from "../components/StatTile";

const AXIS = { stroke: "#3d4d56", fontSize: 10, fontFamily: "monospace" };

const TYPES: { value: ExperimentType; label: string; hint: string }[] = [
  { value: "sequential", label: "Sequential", hint: "1 process baseline" },
  { value: "local_parallel", label: "Local parallel", hint: "multiprocessing on master" },
  { value: "distributed", label: "Distributed", hint: "master + N workers" },
  { value: "scalability", label: "Scalability", hint: "1 · 2 · 4 · 6 · 9 workers" },
];

const STATUS_TONE: Record<string, string> = {
  pending: "border-ink-600 bg-ink-800 text-mist-300",
  running: "border-[#4a3716] bg-[#1d1608] text-[#fbd99a]",
  completed: "border-[#3c5220] bg-[#141f0c] text-[#cdf98a]",
  failed: "border-[#4d2525] bg-[#1c0d0d] text-[#ffb3b3]",
  cancelled: "border-ink-600 bg-ink-800 text-mist-400",
};

export function PerformancePage() {
  const { overview } = useCluster();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    type: "distributed" as ExperimentType,
    workers: "1",
    pages: "120",
    depth: "2",
    batch: "5",
    delay: "0",
    repeat: "3",
    scheduling: "dynamic" as "dynamic" | "static",
  });
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const experimentsQuery = useQuery({
    queryKey: ["experiments"],
    queryFn: () => api.experiments(),
    refetchInterval: 2000,
  });

  const experiments = experimentsQuery.data ?? [];
  const running = experiments.find((exp) => exp.status === "running" || exp.status === "pending") ?? null;
  const latestSuite = experiments.find((exp) => exp.experiment_type === "scalability");

  const groupQuery = useQuery({
    queryKey: ["experiments", "group", latestSuite?.experiment_id],
    queryFn: () => api.experiments(latestSuite?.experiment_id),
    enabled: Boolean(latestSuite?.experiment_id),
  });

  const runMutation = useMutation({
    mutationFn: () =>
      api.runExperiment({
        experiment_type: form.type,
        worker_count: Number(form.workers) || 1,
        maximum_pages: Number(form.pages) || 100,
        maximum_depth: Number(form.depth) || 1,
        batch_size: Number(form.batch) || 5,
        domain_delay: Number(form.delay) || 0,
        repeat: Number(form.repeat) || 3,
        scheduling_mode: form.scheduling,
      }),
    onSuccess: (exp) => {
      setError(null);
      setNotice(`Eksperimen ${exp.experiment_id} dijalankan.`);
      queryClient.invalidateQueries({ queryKey: ["experiments"] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => api.cancelExperiment(id),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["experiments"] }),
  });

  const recent = experiments.filter((exp) => exp.status === "completed" && exp.experiment_type !== "scalability");
  const latest = recent[0];
  const activeWorkers = overview?.active_workers ?? 0;

  const curve = (groupQuery.data ?? [])
    .filter((exp) => exp.experiment_type === "distributed" && exp.status === "completed")
    .sort((a, b) => a.worker_count - b.worker_count)
    .map((exp) => ({
      workers: `${exp.worker_count}w`,
      speedup: exp.speedup ?? 0,
      efficiency: exp.efficiency ?? 0,
      time: Math.round(exp.execution_time_ms),
    }));

  const update = (key: keyof typeof form, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const sequential = form.type === "sequential";
  const scalability = form.type === "scalability";

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          label="Last execution"
          value={latest ? `${(latest.execution_time_ms / 1000).toFixed(2)}s` : "—"}
          hint={latest ? titleCase(latest.experiment_type) : "no run yet"}
          icon={<Gauge className="size-4" />}
        />
        <StatTile
          label="Speedup"
          value={latest?.speedup ? `${latest.speedup.toFixed(2)}×` : "—"}
          hint={latest?.baseline_id ? "vs sequential baseline" : "baseline belum ada"}
          tone="signal"
          icon={<TrendingUp className="size-4" />}
        />
        <StatTile
          label="Efficiency"
          value={latest?.efficiency ? `${latest.efficiency.toFixed(1)}%` : "—"}
          hint={latest ? `${latest.worker_count} worker` : "—"}
          tone="ice"
        />
        <StatTile
          label="Throughput"
          value={latest ? latest.throughput.toFixed(1) : "—"}
          hint="pages / second"
          tone="amber"
          icon={<Activity className="size-4" />}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
        <Panel
          eyebrow="benchmark suite"
          title="Run experiment"
          actions={<span className="chip"><FlaskConical className="size-3" /> {activeWorkers} workers</span>}
          bodyClassName="p-4"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block space-y-1.5 sm:col-span-2">
              <span className="eyebrow">experiment type</span>
              <select
                className="field"
                value={form.type}
                onChange={(event) => update("type", event.target.value)}
                disabled={Boolean(running)}
              >
                {TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label} — {type.hint}
                  </option>
                ))}
              </select>
            </label>
            <Num label="workers" value={form.workers} onChange={(v) => update("workers", v)} disabled={sequential || scalability} />
            <Num label="maximum pages" value={form.pages} onChange={(v) => update("pages", v)} disabled={Boolean(running)} />
            <Num label="maximum depth" value={form.depth} onChange={(v) => update("depth", v)} disabled={Boolean(running)} />
            <Num label="batch size" value={form.batch} onChange={(v) => update("batch", v)} disabled={Boolean(running)} />
            <Num label="domain delay (s)" value={form.delay} onChange={(v) => update("delay", v)} disabled={Boolean(running)} />
            <Num label="repeat (median)" value={form.repeat} onChange={(v) => update("repeat", v)} disabled={Boolean(running)} />
            <label className="block space-y-1.5 sm:col-span-2">
              <span className="eyebrow">scheduling</span>
              <select
                className="field"
                value={form.scheduling}
                onChange={(event) => update("scheduling", event.target.value)}
                disabled={Boolean(running)}
              >
                <option value="dynamic">Dynamic load balancing</option>
                <option value="static">Static round-robin</option>
              </select>
            </label>
          </div>

          <div className="mt-3.5 flex flex-wrap items-center gap-2 border-t border-ink-800 pt-3">
            <button
              className="btn btn-primary"
              disabled={runMutation.isPending || Boolean(running) || (form.type === "distributed" && activeWorkers === 0)}
              onClick={() => runMutation.mutate()}
            >
              {runMutation.isPending || running ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
              {running ? "running…" : "run experiment"}
            </button>
            <span className="font-mono text-[0.62rem] leading-relaxed text-mist-500">
              benchmark memakai bench site master; hasil disimpan otomatis ke Experiment History.
            </span>
          </div>

          {error ? (
            <div className="mt-3 rounded border border-[#4d2525] bg-[#1c0d0d] px-3 py-2 font-mono text-[0.66rem] text-[#ffb3b3]">
              {error}
            </div>
          ) : null}
          {notice ? (
            <div className="mt-3 rounded border border-[#3c5220] bg-[#0f1709] px-3 py-2 font-mono text-[0.66rem] text-[#cdf98a]">
              {notice}
            </div>
          ) : null}
        </Panel>

        <Panel
          eyebrow="current run"
          title={running ? running.experiment_id : "Idle"}
          actions={
            running ? (
              <button
                className="btn !px-2 !py-1"
                onClick={() => cancelMutation.mutate(running.experiment_id)}
                disabled={cancelMutation.isPending}
              >
                <Ban className="size-3.5 text-danger" /> cancel
              </button>
            ) : (
              <span className={`chip ${STATUS_TONE.completed}`}>ready</span>
            )
          }
          bodyClassName="p-4"
        >
          {running ? (
            <RunProgress experiment={running} />
          ) : (
            <div className="space-y-2 font-mono text-[0.7rem] text-mist-500">
              <p>Pilih tipe eksperimen lalu jalankan. Suite scalability menjalankan sequential baseline + 1/2/4/6/9 worker otomatis (dilewati bila worker kurang).</p>
              <p className="text-mist-400">
                workload key memastikan speedup hanya dibandingkan dengan baseline yang setara
                (seed, pages, depth, batch, timeout).
              </p>
            </div>
          )}

          {latest ? (
            <dl className="mt-4 space-y-1.5 border-t border-ink-800 pt-3 font-mono text-[0.68rem]">
              <MetricRow label="pages" value={`${latest.pages_ok} ok · ${latest.pages_failed} fail`} />
              <MetricRow label="cpu / mem avg" value={`${latest.cpu_utilization.toFixed(0)}% / ${latest.memory_utilization.toFixed(0)}%`} />
              <MetricRow label="workers" value={`${latest.worker_count}`} />
              <MetricRow label="scheduling" value={latest.scheduling_mode} />
            </dl>
          ) : null}
        </Panel>
      </div>

      <Panel
        eyebrow={latestSuite ? `suite ${latestSuite.experiment_id}` : "scalability"}
        title="Speedup & efficiency curve"
        actions={
          latestSuite ? (
            <a className="btn btn-ghost" href={api.experimentExportUrl("csv")} download>
              export csv
            </a>
          ) : null
        }
        bodyClassName="p-4"
      >
        {curve.length ? (
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={curve} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="#1d282f" vertical={false} />
                <XAxis dataKey="workers" tick={AXIS} axisLine={false} tickLine={false} />
                <YAxis yAxisId="left" tick={AXIS} axisLine={false} tickLine={false} width={38} />
                <YAxis yAxisId="right" orientation="right" unit="%" tick={AXIS} axisLine={false} tickLine={false} width={46} />
                <Tooltip
                  contentStyle={{
                    background: "#0e1418",
                    border: "1px solid #2b3941",
                    borderRadius: 8,
                    fontFamily: "monospace",
                    fontSize: 11,
                  }}
                />
                <Line yAxisId="left" type="monotone" dataKey="speedup" name="Speedup ×" stroke="#b8f24a" strokeWidth={2} dot={{ r: 3 }} />
                <Line yAxisId="right" type="monotone" dataKey="efficiency" name="Efficiency %" stroke="#52d9e8" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="font-mono text-[0.7rem] text-mist-500">
            Jalankan tipe <span className="text-mist-300">Scalability</span> untuk membuat kurva speedup
            dan efficiency terhadap jumlah worker. Butuh minimal satu worker aktif; langkah yang
            melebihi jumlah worker dilewati.
          </p>
        )}
      </Panel>

      <Panel eyebrow="latest measurements" title="Recent experiments" bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[880px] text-left font-mono text-[0.68rem]">
            <thead>
              <tr className="border-b border-ink-800 text-[0.6rem] uppercase tracking-[0.14em] text-mist-500">
                <th className="px-4 py-2.5 font-normal">type</th>
                <th className="px-4 py-2.5 text-right font-normal">workers</th>
                <th className="px-4 py-2.5 text-right font-normal">exec</th>
                <th className="px-4 py-2.5 text-right font-normal">pages</th>
                <th className="px-4 py-2.5 text-right font-normal">speedup</th>
                <th className="px-4 py-2.5 text-right font-normal">efficiency</th>
                <th className="px-4 py-2.5 text-right font-normal">cpu</th>
                <th className="px-4 py-2.5 font-normal">status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-800">
              {experiments.slice(0, 8).map((exp) => (
                <tr key={exp.experiment_id} className="hover:bg-ink-850/60">
                  <td className="px-4 py-2.5 text-mist-200">{titleCase(exp.experiment_type)}</td>
                  <td className="px-4 py-2.5 text-right">{exp.worker_count}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{(exp.execution_time_ms / 1000).toFixed(2)}s</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{exp.pages_ok}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-signal">
                    {exp.speedup ? `${exp.speedup.toFixed(2)}×` : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-ice">
                    {exp.efficiency ? `${exp.efficiency.toFixed(0)}%` : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{exp.cpu_utilization.toFixed(0)}%</td>
                  <td className="px-4 py-2.5">
                    <span className={`chip ${STATUS_TONE[exp.status] ?? ""}`}>{exp.status}</span>
                  </td>
                </tr>
              ))}
              {!experiments.length ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-mist-500">
                    belum ada eksperimen tercatat
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function RunProgress({ experiment }: { experiment: Experiment }) {
  const total = Math.max(experiment.total_pages, 1);
  const percent = Math.min(100, (experiment.progress_pages / total) * 100);
  const elapsed = experiment.finished_at
    ? experiment.execution_time_ms
    : Date.now() - new Date(experiment.created_at).getTime();

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="chip border-[#4a3716] bg-[#1d1608] text-[#fbd99a]">{experiment.status}</span>
        <span className="font-mono text-[0.66rem] text-mist-400">
          {(elapsed / 1000).toFixed(1)}s
        </span>
      </div>
      <div>
        <div className="h-1.5 w-full overflow-hidden rounded bg-ink-700">
          <div className="h-1.5 rounded bg-signal transition-all" style={{ width: `${percent}%` }} />
        </div>
        <div className="mt-1.5 flex justify-between font-mono text-[0.62rem] text-mist-500">
          <span>
            {experiment.progress_pages}/{experiment.total_pages} pages
          </span>
          <span>
            {titleCase(experiment.experiment_type)} · {experiment.worker_count} worker
          </span>
        </div>
      </div>
      {experiment.error ? (
        <div className="rounded border border-[#4d2525] bg-[#1c0d0d] px-3 py-2 font-mono text-[0.64rem] text-[#ffb3b3]">
          {experiment.error}
        </div>
      ) : null}
    </div>
  );
}

function Num({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="eyebrow">{label}</span>
      <input
        className="field"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        inputMode="numeric"
      />
    </label>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-mist-500">{label}</dt>
      <dd className="text-right text-mist-200">{value}</dd>
    </div>
  );
}
