import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Download, History, LineChart as LineChartIcon } from "lucide-react";
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
import { formatAgo, titleCase } from "../lib/format";
import type { Experiment } from "../lib/types";
import { Panel, EmptyState } from "../components/Panel";

const AXIS = { stroke: "#3d4d56", fontSize: 10, fontFamily: "monospace" };

const STATUS_TONE: Record<string, string> = {
  pending: "border-ink-600 bg-ink-800 text-mist-300",
  running: "border-[#4a3716] bg-[#1d1608] text-[#fbd99a]",
  completed: "border-[#3c5220] bg-[#141f0c] text-[#cdf98a]",
  failed: "border-[#4d2525] bg-[#1c0d0d] text-[#ffb3b3]",
  cancelled: "border-ink-600 bg-ink-800 text-mist-400",
};

export function ExperimentsPage() {
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const experimentsQuery = useQuery({
    queryKey: ["experiments"],
    queryFn: () => api.experiments(),
    refetchInterval: 5000,
  });

  const detailQuery = useQuery({
    queryKey: ["experiments", "detail", selectedId],
    queryFn: () => api.experiment(selectedId as string, true),
    enabled: Boolean(selectedId),
  });

  const all = experimentsQuery.data ?? [];
  const rows = typeFilter ? all.filter((exp) => exp.experiment_type === typeFilter) : all;
  const selected: Experiment | undefined = detailQuery.data;
  const samples = (selected?.samples ?? []).map((sample) => ({
    t: Math.round(sample.ts_offset_ms / 1000),
    cpu: sample.cpu_usage,
    mem: sample.memory_usage,
    pages: sample.pages_done,
  }));

  return (
    <div className="space-y-4">
      <Panel
        eyebrow={`${rows.length} recorded`}
        title="Experiment History"
        actions={
          <>
            <select
              className="field !w-auto !py-1"
              value={typeFilter}
              onChange={(event) => setTypeFilter(event.target.value)}
            >
              <option value="">all types</option>
              {["sequential", "local_parallel", "distributed", "scalability"].map((type) => (
                <option key={type} value={type}>
                  {titleCase(type)}
                </option>
              ))}
            </select>
            <a className="btn btn-ghost" href={api.experimentExportUrl("csv")} download>
              <Download className="size-3.5" /> csv
            </a>
            <a className="btn btn-ghost" href={api.experimentExportUrl("json")} download>
              <Download className="size-3.5" /> json
            </a>
          </>
        }
        bodyClassName="p-0"
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1040px] text-left font-mono text-[0.68rem]">
            <thead>
              <tr className="border-b border-ink-800 text-[0.6rem] uppercase tracking-[0.14em] text-mist-500">
                <th className="px-4 py-2.5 font-normal">experiment</th>
                <th className="px-4 py-2.5 font-normal">type</th>
                <th className="px-4 py-2.5 text-right font-normal">workers</th>
                <th className="px-4 py-2.5 text-right font-normal">exec</th>
                <th className="px-4 py-2.5 text-right font-normal">pages</th>
                <th className="px-4 py-2.5 text-right font-normal">speedup</th>
                <th className="px-4 py-2.5 text-right font-normal">eff.</th>
                <th className="px-4 py-2.5 text-right font-normal">throughput</th>
                <th className="px-4 py-2.5 text-right font-normal">cpu/mem</th>
                <th className="px-4 py-2.5 font-normal">when</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-800">
              {rows.map((exp) => (
                <tr
                  key={exp.experiment_id}
                  onClick={() => setSelectedId(exp.experiment_id)}
                  className={`cursor-pointer hover:bg-ink-850/60 ${
                    selectedId === exp.experiment_id ? "bg-ink-850/80" : ""
                  }`}
                >
                  <td className="px-4 py-2.5">
                    <div className="text-mist-200">{exp.experiment_id}</div>
                    {exp.group_id && exp.group_id !== exp.experiment_id ? (
                      <div className="text-[0.58rem] text-mist-500">suite {exp.group_id}</div>
                    ) : null}
                  </td>
                  <td className="px-4 py-2.5 text-mist-400">{titleCase(exp.experiment_type)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{exp.worker_count}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">
                    {exp.execution_time_ms ? `${(exp.execution_time_ms / 1000).toFixed(2)}s` : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{exp.pages_ok}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-signal">
                    {exp.speedup ? `${exp.speedup.toFixed(2)}×` : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-ice">
                    {exp.efficiency ? `${exp.efficiency.toFixed(0)}%` : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{exp.throughput.toFixed(1)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-mist-400">
                    {exp.cpu_utilization.toFixed(0)}/{exp.memory_utilization.toFixed(0)}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`chip ${STATUS_TONE[exp.status] ?? ""}`}>{exp.status}</span>
                    <div className="mt-1 text-[0.58rem] text-mist-500">{formatAgo(exp.created_at)}</div>
                  </td>
                </tr>
              ))}
              {!rows.length ? (
                <tr>
                  <td colSpan={10} className="px-4 py-10">
                    <EmptyState
                      icon={<History className="size-6" />}
                      title="Belum ada eksperimen"
                      body="Jalankan benchmark dari Performance Lab. Setiap run menyimpan execution time, speedup, efficiency, throughput, dan sampel resource."
                    />
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Panel
          eyebrow="resource trace"
          title={selected ? `${selected.experiment_id} · ${titleCase(selected.experiment_type)}` : "Select an experiment"}
          actions={
            selected ? (
              <span className={`chip ${STATUS_TONE[selected.status] ?? ""}`}>{selected.status}</span>
            ) : null
          }
          bodyClassName="p-4"
        >
          {selected && samples.length ? (
            <div className="h-[240px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={samples} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid stroke="#1d282f" vertical={false} />
                  <XAxis dataKey="t" unit="s" tick={AXIS} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} unit="%" tick={AXIS} axisLine={false} tickLine={false} width={38} />
                  <Tooltip
                    contentStyle={{
                      background: "#0e1418",
                      border: "1px solid #2b3941",
                      borderRadius: 8,
                      fontFamily: "monospace",
                      fontSize: 11,
                    }}
                  />
                  <Line type="monotone" dataKey="cpu" name="CPU %" stroke="#b8f24a" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="mem" name="MEM %" stroke="#52d9e8" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState
              icon={<LineChartIcon className="size-6" />}
              title={selected ? "Tidak ada sampel" : "Pilih baris eksperimen"}
              body={
                selected
                  ? "Eksperimen ini tidak menghasilkan sampel resource (dibatalkan atau gagal sebelum sampling)."
                  : "Klik salah satu baris untuk melihat trace CPU/memory dan konfigurasi workload."
              }
            />
          )}
        </Panel>

        <Panel eyebrow="configuration" title="Workload snapshot" bodyClassName="p-4">
          {selected ? (
            <>
              <dl className="space-y-1.5 font-mono text-[0.68rem]">
                <Row label="workload key" value={selected.workload_key} />
                <Row label="scheduling" value={selected.scheduling_mode} />
                <Row label="workers" value={`${selected.worker_count}`} />
                <Row label="pages" value={`${selected.pages_ok} ok · ${selected.pages_failed} fail`} />
                <Row label="execution" value={`${(selected.execution_time_ms / 1000).toFixed(2)} s`} />
                <Row label="throughput" value={`${selected.throughput.toFixed(2)} p/s`} />
                <Row label="speedup" value={selected.speedup ? `${selected.speedup.toFixed(3)}×` : "—"} />
                <Row label="efficiency" value={selected.efficiency ? `${selected.efficiency.toFixed(2)}%` : "—"} />
                <Row label="cpu / mem avg" value={`${selected.cpu_utilization.toFixed(1)}% / ${selected.memory_utilization.toFixed(1)}%`} />
                <Row label="baseline" value={selected.baseline_id ?? "—"} />
              </dl>
              <pre className="mt-3 max-h-[180px] overflow-auto rounded border border-ink-700 bg-ink-900 p-3 font-mono text-[0.62rem] leading-relaxed text-mist-400">
{JSON.stringify(selected.config, null, 2)}
              </pre>
            </>
          ) : (
            <p className="font-mono text-[0.68rem] leading-relaxed text-mist-500">
              Konfigurasi workload (seed, pages, depth, batch, timeout, scheduling) tersimpan bersama
              setiap eksperimen agar hasil dapat direproduksi untuk lampiran laporan.
            </p>
          )}
        </Panel>
      </div>

      <div className="panel flex items-center gap-3 px-4 py-3">
        <LineChartIcon className="size-4 text-ice" />
        <span className="font-mono text-[0.64rem] leading-relaxed text-mist-400">
          Efficiency &gt; 100% pada 1 worker berarti proses multiprocessing per node memberi
          paralelisme tambahan di luar jumlah node — catat sebagai temuan analisis, bukan error.
        </span>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="shrink-0 text-mist-500">{label}</dt>
      <dd className="min-w-0 break-all text-right text-mist-200">{value}</dd>
    </div>
  );
}
