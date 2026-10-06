"use client";

import { useApi } from "@/hooks/use-api";
import { endpoints } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { HealthResponse } from "@/lib/types";

/** Live backend status: green dot when the API and model are loaded. */
export function StatusPill({ className }: { className?: string }) {
  const { data, error, isLoading } = useApi<HealthResponse>(endpoints.health, { refreshInterval: 30_000 });
  const online = !!data && !error;
  const label = isLoading ? "Connecting" : online ? "Model online" : "API offline";
  return (
    <span
      role="status"
      title={online ? `${data.model} · trained on ${data.training_tests} FLEX tests` : "Start the FastAPI backend"}
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-[0.6875rem] uppercase tracking-wider",
        online ? "border-risk-low/30 text-risk-low" : isLoading ? "border-white/10 text-ink-3" : "border-risk-high/30 text-risk-high",
        className,
      )}
    >
      <span className="relative flex size-2">
        {online && <span className="absolute inline-flex size-full animate-ping rounded-full bg-risk-low/60" />}
        <span className={cn("relative inline-flex size-2 rounded-full", online ? "bg-risk-low" : isLoading ? "bg-ink-3" : "bg-risk-high")} />
      </span>
      {label}
    </span>
  );
}
