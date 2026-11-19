import clsx from "clsx";
import {
  Activity,
  Boxes,
  FlaskConical,
  Gauge,
  History,
  LayoutDashboard,
  ListChecks,
  Network,
  Radar,
  Search,
  Settings,
  Waves,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/discovery", label: "Node Discovery", icon: Radar },
  { to: "/topology", label: "Cluster", icon: Network },
  { to: "/jobs", label: "Crawl Jobs", icon: Boxes },
  { to: "/tasks", label: "Task Monitor", icon: ListChecks },
  { to: "/results", label: "Results", icon: Search },
  { to: "/performance", label: "Performance Lab", icon: Gauge },
  { to: "/experiments", label: "Experiment History", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export function Sidebar({
  connected,
  clusterId,
  activeWorkers,
}: {
  connected: boolean;
  clusterId: string | null;
  activeWorkers: number;
}) {
  return (
    <aside className="flex w-[236px] shrink-0 flex-col border-r border-ink-800 bg-ink-900/80 backdrop-blur">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="grid size-9 place-items-center rounded-lg border border-signal/30 bg-signal/10">
          <Waves className="size-4.5 text-signal" />
        </div>
        <div>
          <div className="font-mono text-[0.82rem] font-bold tracking-[0.14em] text-mist-100">
            CRAWLMESH
          </div>
          <div className="font-mono text-[0.58rem] uppercase tracking-[0.18em] text-mist-500">
            distributed crawler
          </div>
        </div>
      </div>

      <nav className="mt-1 flex flex-1 flex-col gap-0.5 px-2.5">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={"end" in item ? item.end : false}
            className={({ isActive }) =>
              clsx(
                "group relative flex items-center gap-2.5 rounded-md px-2.5 py-2 font-mono text-[0.72rem] tracking-wide transition",
                isActive
                  ? "bg-ink-750 text-mist-100"
                  : "text-mist-400 hover:bg-ink-850 hover:text-mist-200",
              )
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={clsx(
                    "absolute left-0 h-4 w-[2px] rounded-full",
                    isActive ? "bg-signal" : "bg-transparent",
                  )}
                />
                <item.icon className={clsx("size-4", isActive ? "text-signal" : "text-mist-500")} />
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="space-y-2.5 border-t border-ink-800 px-4 py-4 font-mono text-[0.62rem] text-mist-500">
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-1.5">
            <Activity className={clsx("size-3.5", connected ? "text-signal" : "text-danger")} />
            {connected ? "stream live" : "stream down"}
          </span>
          <span className={clsx("size-1.5 rounded-full", connected ? "bg-signal live-dot" : "bg-danger")} />
        </div>
        <div className="flex items-center justify-between">
          <span>cluster</span>
          <span className="text-mist-300">{clusterId ?? "not init"}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>active workers</span>
          <span className="text-mist-300">{activeWorkers}/9</span>
        </div>
        <div className="flex items-center justify-between pt-1 text-mist-500/70">
          <span className="inline-flex items-center gap-1">
            <FlaskConical className="size-3" /> UAS · v0.1.0
          </span>
        </div>
      </div>
    </aside>
  );
}
