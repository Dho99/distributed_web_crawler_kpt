import clsx from "clsx";
import type { ReactNode } from "react";

export function Panel({
  title,
  eyebrow,
  actions,
  children,
  className,
  bodyClassName,
}: {
  title?: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section className={clsx("panel flex min-w-0 flex-col", className)}>
      {(title || actions) && (
        <div className="panel-head">
          <div className="min-w-0">
            {eyebrow ? <div className="eyebrow">{eyebrow}</div> : null}
            {title ? (
              <h2 className="truncate text-[0.86rem] font-semibold text-mist-100">{title}</h2>
            ) : null}
          </div>
          {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
        </div>
      )}
      <div className={clsx("min-w-0 flex-1", bodyClassName ?? "p-4")}>{children}</div>
    </section>
  );
}

export function EmptyState({
  icon,
  title,
  body,
  action,
}: {
  icon?: ReactNode;
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-ink-700 px-6 py-10 text-center">
      {icon ? <div className="text-mist-500">{icon}</div> : null}
      <div className="text-[0.85rem] font-medium text-mist-200">{title}</div>
      <p className="max-w-sm text-[0.75rem] leading-relaxed text-mist-500">{body}</p>
      {action ? <div className="mt-1.5">{action}</div> : null}
    </div>
  );
}
