import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ChevronLeft, ChevronRight, Download, FileSearch, Filter, Search } from "lucide-react";
import { api } from "../lib/api";
import { useCluster } from "../lib/cluster-context";
import { formatAgo } from "../lib/format";
import type { ResultRow } from "../lib/types";
import { Panel, EmptyState } from "../components/Panel";

const PAGE_SIZE = 50;

export function ResultsPage() {
  const { overview } = useCluster();
  const [jobFilter, setJobFilter] = useState("");
  const [workerFilter, setWorkerFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [q, setQ] = useState("");
  const [appliedQ, setAppliedQ] = useState("");
  const [offset, setOffset] = useState(0);

  const jobsQuery = useQuery({ queryKey: ["jobs"], queryFn: api.jobs });
  const resultsQuery = useQuery({
    queryKey: ["results", jobFilter, workerFilter, statusFilter, appliedQ, offset],
    queryFn: () =>
      api.results({
        jobId: jobFilter || undefined,
        worker: workerFilter || undefined,
        status: statusFilter || undefined,
        q: appliedQ || undefined,
        offset,
        limit: PAGE_SIZE,
      }),
    refetchInterval: 5000,
  });

  const jobs = jobsQuery.data ?? [];
  const workers = (overview?.nodes ?? []).filter((node) => node.role === "worker");
  const data = resultsQuery.data ?? { total: 0, items: [] };
  const exportHref = api.exportUrl("csv", jobFilter || undefined);

  const resetPaging = () => setOffset(0);

  return (
    <div className="space-y-4">
      <Panel
        eyebrow={`${data.total} rows`}
        title="Results Explorer"
        actions={
          <>
            <a className="btn btn-ghost" href={exportHref} download>
              <Download className="size-3.5" /> csv
            </a>
            <a className="btn btn-ghost" href={api.exportUrl("json", jobFilter || undefined)} download>
              <Download className="size-3.5" /> json
            </a>
          </>
        }
        bodyClassName="p-0"
      >
        <div className="flex flex-wrap items-center gap-2 border-b border-ink-800 px-4 py-3">
          <form
            className="relative min-w-[220px] flex-1"
            onSubmit={(event) => {
              event.preventDefault();
              setAppliedQ(q.trim());
              resetPaging();
            }}
          >
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-mist-500" />
            <input
              className="field pl-8"
              placeholder="search url / title — enter"
              value={q}
              onChange={(event) => setQ(event.target.value)}
            />
          </form>
          <select
            className="field !w-auto"
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value);
              resetPaging();
            }}
          >
            <option value="">all http status</option>
            {["200", "301", "302", "403", "404", "500"].map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
          <select
            className="field !w-auto"
            value={workerFilter}
            onChange={(event) => {
              setWorkerFilter(event.target.value);
              resetPaging();
            }}
          >
            <option value="">all workers</option>
            {workers.map((worker) => (
              <option key={worker.worker_id} value={worker.worker_id}>
                {worker.hostname}
              </option>
            ))}
          </select>
          <select
            className="field !w-auto"
            value={jobFilter}
            onChange={(event) => {
              setJobFilter(event.target.value);
              resetPaging();
            }}
          >
            <option value="">all jobs</option>
            {jobs.map((job) => (
              <option key={job.job_id} value={job.job_id}>
                {job.job_name}
              </option>
            ))}
          </select>
          <span className="chip">
            <Filter className="size-3" /> {data.items.length} shown
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1020px] text-left font-mono text-[0.68rem]">
            <thead>
              <tr className="border-b border-ink-800 text-[0.6rem] uppercase tracking-[0.14em] text-mist-500">
                <th className="px-4 py-2.5 font-normal">url</th>
                <th className="px-4 py-2.5 font-normal">http</th>
                <th className="px-4 py-2.5 font-normal">title</th>
                <th className="px-4 py-2.5 text-right font-normal">links</th>
                <th className="px-4 py-2.5 text-right font-normal">response</th>
                <th className="px-4 py-2.5 font-normal">worker</th>
                <th className="px-4 py-2.5 font-normal">crawled</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-800">
              {data.items.map((row) => (
                <ResultTableRow key={row.result_id} row={row} />
              ))}
              {!data.items.length ? (
                <tr>
                  <td colSpan={7} className="px-4 py-10">
                    <EmptyState
                      icon={<FileSearch className="size-6" />}
                      title="Belum ada hasil"
                      body="Jalankan crawl job. Hasil muncul di sini setelah worker mengirim batch result dan master menyimpannya secara idempoten."
                    />
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-ink-800 px-4 py-2.5 font-mono text-[0.64rem] text-mist-500">
          <span>
            {data.total ? offset + 1 : 0}–{Math.min(offset + PAGE_SIZE, data.total)} of {data.total}
          </span>
          <div className="flex items-center gap-1.5">
            <button
              className="btn btn-ghost !px-2 !py-1"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              <ChevronLeft className="size-3.5" />
            </button>
            <button
              className="btn btn-ghost !px-2 !py-1"
              disabled={offset + PAGE_SIZE >= data.total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              <ChevronRight className="size-3.5" />
            </button>
          </div>
        </div>
      </Panel>
    </div>
  );
}

function ResultTableRow({ row }: { row: ResultRow }) {
  const url = row.url.replace(/^https?:\/\//, "");
  return (
    <tr className="hover:bg-ink-850/70">
      <td className="max-w-[320px] px-4 py-2.5">
        <a
          href={row.url}
          target="_blank"
          rel="noreferrer"
          className="block truncate text-ice hover:text-signal"
          title={row.url}
        >
          {url}
        </a>
        <div className="truncate text-[0.58rem] text-mist-500/70">{row.worker_id}</div>
      </td>
      <td className="px-4 py-2.5">
        <span className={row.http_status >= 400 ? "text-danger" : "text-signal"}>{row.http_status}</span>
      </td>
      <td className="max-w-[260px] truncate px-4 py-2.5 text-mist-300" title={row.title}>
        {row.title || "—"}
      </td>
      <td className="px-4 py-2.5 text-right tabular-nums text-mist-300">{row.links_found}</td>
      <td className="px-4 py-2.5 text-right tabular-nums text-mist-300">
        {row.response_time_ms ? `${row.response_time_ms.toFixed(0)} ms` : "—"}
      </td>
      <td className="px-4 py-2.5 text-mist-400">{row.worker_id}</td>
      <td className="px-4 py-2.5 text-mist-500">{formatAgo(row.crawled_at)}</td>
    </tr>
  );
}
