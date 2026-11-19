import clsx from "clsx";
import type { ReactNode } from "react";

export function StatTile({
  label,
  value,
  hint,
  icon,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  tone?: "default" | "signal" | "ice" | "amber" | "danger";
}) {
  const toneClass = {
    default: "text-mist-100",
    signal: "text-signal",
    ice: "text-ice",
    amber: "text-amber",
    danger: "text-danger",
  }[tone];

  return (
    <div className="panel px-4 py-3.5">
      <div className="flex items-start justify-between gap-3">
        <span className="eyebrow">{label}</span>
        {icon ? <span className="text-mist-500">{icon}</span> : null}
      </div>
      <div className={clsx("mt-2 font-mono text-2xl leading-none tracking-tight", toneClass)}>{value}</div>
      {hint ? <div className="mt-1.5 font-mono text-[0.65rem] text-mist-500">{hint}</div> : null}
    </div>
  );
}
