import clsx from "clsx";
import type { NodeStatus } from "../lib/types";
import { STATUS_LABEL } from "../lib/types";

const STYLES: Record<NodeStatus, { dot: string; text: string; border: string; bg: string }> = {
  online: { dot: "bg-[#b8f24a]", text: "text-[#cdf98a]", border: "border-[#3c5220]", bg: "bg-[#141f0c]" },
  idle: { dot: "bg-[#52d9e8]", text: "text-[#a9eef5]", border: "border-[#1d4450]", bg: "bg-[#0b1a1f]" },
  busy: { dot: "bg-[#f5b544]", text: "text-[#fbd99a]", border: "border-[#4a3716]", bg: "bg-[#1d1608]" },
  pending: { dot: "bg-[#8b9ca6]", text: "text-[#c2cdd3]", border: "border-[#2b3941]", bg: "bg-[#131a1e]" },
  discovered: { dot: "bg-[#8b9ca6]", text: "text-[#c2cdd3]", border: "border-[#2b3941]", bg: "bg-[#131a1e]" },
  degraded: { dot: "bg-[#f5b544]", text: "text-[#fbd99a]", border: "border-[#4a3716]", bg: "bg-[#1d1608]" },
  offline: { dot: "bg-[#ff6b6b]", text: "text-[#ffb3b3]", border: "border-[#4d2525]", bg: "bg-[#1c0d0d]" },
  removed: { dot: "bg-[#3d4d56]", text: "text-[#8b9ca6]", border: "border-[#2b3941]", bg: "bg-[#131a1e]" },
};

export function StatusPill({ status, label }: { status: NodeStatus; label?: string }) {
  const style = STYLES[status] ?? STYLES.pending;
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono text-[0.62rem] uppercase tracking-[0.12em]",
        style.border,
        style.bg,
        style.text,
      )}
    >
      <span className={clsx("size-1.5 rounded-full", style.dot, status !== "offline" && "live-dot")} />
      {label ?? STATUS_LABEL[status]}
    </span>
  );
}
