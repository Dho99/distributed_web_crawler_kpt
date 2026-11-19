import { type ReactNode } from "react";
import { Lock } from "lucide-react";

export function PhaseGate({
  phase,
  title,
  acceptance,
  children,
}: {
  phase: string;
  title: string;
  acceptance: string;
  children: ReactNode;
}) {
  return (
    <div className="panel border-ink-700 bg-ink-900/60 p-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-md border border-ink-600 bg-ink-800">
          <Lock className="size-3.5 text-mist-500" />
        </div>
        <div className="min-w-0">
          <div className="eyebrow">{phase} · gate</div>
          <div className="text-[0.85rem] font-semibold text-mist-100">{title}</div>
          <p className="mt-1 text-[0.74rem] leading-relaxed text-mist-500">{children}</p>
          <div className="mt-2 chip border-ink-600 font-mono">{acceptance}</div>
        </div>
      </div>
    </div>
  );
}
