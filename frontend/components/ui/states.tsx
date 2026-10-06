import { CircleAlert, Inbox, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

/** Shimmering placeholder blocks while data loads. */
export function LoadingState({ rows = 3, className, label = "Loading" }: { rows?: number; className?: string; label?: string }) {
  return (
    <div role="status" aria-live="polite" className={cn("space-y-3", className)}>
      <span className="sr-only">{label}…</span>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-4 animate-pulse rounded-md bg-white/[0.06]" style={{ width: `${92 - i * 14}%` }} />
      ))}
    </div>
  );
}

export function EmptyState({ title, children, icon }: { title: string; children?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-12 text-center">
      <div className="grid size-12 place-items-center rounded-full border border-white/10 bg-white/[0.04] text-ink-2">
        {icon ?? <Inbox className="size-5" aria-hidden="true" />}
      </div>
      <h3 className="font-display text-lg font-semibold text-ink">{title}</h3>
      {children && <div className="max-w-md text-sm text-ink-2">{children}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 rounded-xl border border-risk-high/30 bg-risk-high/[0.06] px-6 py-8 text-center">
      <CircleAlert className="size-6 text-risk-high" aria-hidden="true" />
      <p className="max-w-md text-sm text-ink-2">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-sm text-ink transition hover:bg-white/[0.06]"
        >
          <RefreshCw className="size-3.5" aria-hidden="true" /> Retry
        </button>
      )}
    </div>
  );
}
