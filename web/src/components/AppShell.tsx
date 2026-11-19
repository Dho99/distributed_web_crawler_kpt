import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Radio } from "lucide-react";
import { Sidebar } from "./Sidebar";
import { useCluster } from "../lib/cluster-context";
import { maskToken } from "../lib/format";

const TITLES: Record<string, { label: string; note: string }> = {
  "/": { label: "Overview", note: "cluster health & live activity" },
  "/discovery": { label: "Node Discovery", note: "find and enrol worker agents" },
  "/topology": { label: "Cluster Topology", note: "master → worker topology" },
  "/jobs": { label: "Crawl Jobs", note: "compose and control crawl workloads" },
  "/tasks": { label: "Task Monitor", note: "live task distribution" },
  "/results": { label: "Results Explorer", note: "aggregated crawl output" },
  "/performance": { label: "Performance Lab", note: "parallel benchmarks" },
  "/experiments": { label: "Experiment History", note: "recorded measurements" },
  "/settings": { label: "Settings", note: "cluster identity & agent setup" },
};

function useClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  return now.toLocaleTimeString("en-GB", { hour12: false });
}

export function AppShell() {
  const location = useLocation();
  const clock = useClock();
  const { overview, connected } = useCluster();
  const meta = TITLES[location.pathname] ?? { label: "CrawlMesh", note: "" };
  const cluster = overview?.cluster ?? null;

  return (
    <div className="flex h-full min-h-screen">
      <Sidebar
        connected={connected}
        clusterId={cluster?.cluster_id ?? null}
        activeWorkers={overview?.active_workers ?? 0}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 border-b border-ink-800 bg-ink-950/85 backdrop-blur">
          <div className="flex items-center justify-between gap-4 px-6 py-3.5">
            <div className="min-w-0">
              <div className="eyebrow">control / {meta.label.toLowerCase()}</div>
              <h1 className="mt-0.5 truncate text-[1.05rem] font-semibold tracking-tight text-mist-100">
                {meta.label}
                <span className="ml-2 font-mono text-[0.68rem] font-normal text-mist-500">
                  {meta.note}
                </span>
              </h1>
            </div>

            <div className="flex items-center gap-2.5">
              <span className="chip">
                <Radio className="size-3 text-ice" />
                {cluster?.master_url ?? "master offline"}
              </span>
              {cluster ? <span className="chip">token {maskToken(cluster.pairing_token)}</span> : null}
              <span className="chip border-ink-700 bg-ink-900 tabular-nums">{clock}</span>
              <span
                className={
                  connected
                    ? "chip border-[#3c5220] bg-[#141f0c] text-[#cdf98a]"
                    : "chip border-[#4d2525] bg-[#1c0d0d] text-[#ffb3b3]"
                }
              >
                <span className={connected ? "size-1.5 rounded-full bg-signal live-dot" : "size-1.5 rounded-full bg-danger"} />
                {connected ? "live" : "offline"}
              </span>
            </div>
          </div>
        </header>

        <main className="min-w-0 flex-1 px-6 py-5">
          <Outlet />
        </main>

        <footer className="border-t border-ink-800 px-6 py-2.5 font-mono text-[0.6rem] uppercase tracking-[0.14em] text-mist-500/70">
          crawlmesh · master–worker orchestration · komputasi paralel &amp; sistem terdistribusi
        </footer>
      </div>
    </div>
  );
}
