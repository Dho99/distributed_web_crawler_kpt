import clsx from "clsx";
import { Cpu, HardDrive, Layers, Timer } from "lucide-react";
import type { NodeInfo } from "../lib/types";
import { formatAgo, formatBytes } from "../lib/format";
import { StatusPill } from "./StatusPill";

function Meter({ value, tone }: { value: number; tone: string }) {
  return (
    <div className="meter">
      <span style={{ width: `${Math.min(100, Math.max(0, value))}%` }} className={tone} />
    </div>
  );
}

export function NodeCard({
  node,
  onSelect,
  selected,
  compact,
}: {
  node: NodeInfo;
  onSelect?: (node: NodeInfo) => void;
  selected?: boolean;
  compact?: boolean;
}) {
  const isMaster = node.role === "master";
  return (
    <button
      type="button"
      onClick={() => onSelect?.(node)}
      className={clsx(
        "panel group w-full px-4 py-3.5 text-left transition",
        onSelect && "hover:border-ink-500",
        selected && "border-signal-dim/70 ring-1 ring-signal/20",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="truncate font-mono text-[0.82rem] font-semibold text-mist-100">
              {node.hostname}
            </span>
            <span
              className={clsx(
                "chip",
                isMaster
                  ? "border-[#3c5220] bg-[#141f0c] text-[#cdf98a]"
                  : "border-ink-600 text-mist-400",
              )}
            >
              {isMaster ? "MASTER" : "WORKER"}
            </span>
          </div>
          <div className="mt-1 font-mono text-[0.66rem] text-mist-500">
            {node.ip_address}:{node.port} · {node.worker_id}
          </div>
        </div>
        <StatusPill status={node.status} />
      </div>

      {!compact ? (
        <>
          <div className="mt-3.5 grid grid-cols-2 gap-3">
            <div>
              <div className="flex items-center justify-between font-mono text-[0.64rem] text-mist-500">
                <span className="inline-flex items-center gap-1">
                  <Cpu className="size-3" /> CPU
                </span>
                <span className="text-mist-300">{node.cpu_usage.toFixed(0)}%</span>
              </div>
              <div className="mt-1">
                <Meter value={node.cpu_usage} tone="bg-signal" />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between font-mono text-[0.64rem] text-mist-500">
                <span className="inline-flex items-center gap-1">
                  <HardDrive className="size-3" /> MEM
                </span>
                <span className="text-mist-300">{node.memory_usage.toFixed(0)}%</span>
              </div>
              <div className="mt-1">
                <Meter value={node.memory_usage} tone="bg-ice" />
              </div>
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[0.64rem] text-mist-500">
            <span className="inline-flex items-center gap-1">
              <Layers className="size-3" /> {node.cpu_cores} cores · pool {node.pool_size}
            </span>
            <span className="inline-flex items-center gap-1">
              <Timer className="size-3" /> {formatAgo(node.last_heartbeat)}
            </span>
            <span className="text-mist-400">{formatBytes(node.memory_total)}</span>
          </div>

          <div className="mt-2.5 flex items-center gap-3 border-t border-ink-700 pt-2 font-mono text-[0.64rem] text-mist-500">
            <span>
              inflight <span className="text-mist-200">{node.inflight}</span>/{node.capacity}
            </span>
            <span>
              done <span className="text-signal">{node.completed_tasks}</span>
            </span>
            <span>
              fail <span className="text-danger">{node.failed_tasks}</span>
            </span>
            {node.child_processes > 0 ? (
              <span className="text-mist-400">{node.child_processes} child procs</span>
            ) : null}
          </div>
        </>
      ) : null}
    </button>
  );
}
