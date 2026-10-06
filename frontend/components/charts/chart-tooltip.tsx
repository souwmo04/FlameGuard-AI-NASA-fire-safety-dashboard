import type { ReactNode } from "react";

/** Dark glass tooltip body used inside Recharts `content` render props. Values lead, labels follow. */
export function ChartTooltip({ title, rows }: { title?: ReactNode; rows: { label: string; value: ReactNode; color?: string }[] }) {
  return (
    <div className="glass min-w-40 rounded-xl bg-space-800/95 px-3 py-2 text-xs shadow-xl">
      {title && <p className="mb-1.5 font-medium text-ink">{title}</p>}
      <dl className="space-y-1">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between gap-4">
            <dt className="flex items-center gap-1.5 text-ink-3">
              {r.color && <span className="h-0.5 w-3 rounded-full" style={{ background: r.color }} aria-hidden="true" />}
              {r.label}
            </dt>
            <dd className="font-mono font-semibold text-ink tabular-nums">{r.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
