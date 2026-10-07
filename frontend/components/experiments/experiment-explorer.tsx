"use client";

import { ChevronLeft, ChevronRight, SearchX } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useMemo, useState, type Dispatch, type SetStateAction } from "react";

import { OutcomeShape } from "@/components/charts/outcome-shape";
import { Panel } from "@/components/dashboard/panel";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import { endpoints } from "@/lib/api";
import { OUTCOME_COLORS, OUTCOME_SHORT, type Outcome } from "@/lib/chart-theme";
import {
  DEFAULT_FILTERS,
  filterExperiments,
  sortExperiments,
  type ExperimentFilters,
  type Sort,
  type SortKey,
} from "@/lib/experiment-filters";
import { formatPercent } from "@/lib/format";
import type { ExperimentList, StatsResponse } from "@/lib/types";

import { ExperimentDrawer } from "./experiment-drawer";
import { ExperimentFiltersBar } from "./experiment-filters";
import { ExperimentTable } from "./experiment-table";

const PAGE_SIZE = 25;
const OUTCOMES: Outcome[] = ["Extinction", "Completion", "Disruption"];

/** Outcome mix of the filtered tests as one stacked bar, with counts. */
function OutcomeMix({ items }: { items: ExperimentList["items"] }) {
  const counts = OUTCOMES.map((o) => ({ o, n: items.filter((e) => e.outcome === o).length }));
  const sustained = items.filter((e) => e.sustained).length;
  return (
    <div className="space-y-2">
      <div className="flex h-2.5 overflow-hidden rounded-full bg-white/[0.05]" role="img"
        aria-label={counts.map((c) => `${c.n} ${OUTCOME_SHORT[c.o].toLowerCase()}`).join(", ")}>
        {counts.map((c) => (
          <span key={c.o} className="h-full transition-[width] duration-500" style={{ width: `${(c.n / Math.max(1, items.length)) * 100}%`, background: OUTCOME_COLORS[c.o] }} />
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-3">
        {counts.map((c) => (
          <span key={c.o} className="flex items-center gap-1.5"><OutcomeShape outcome={c.o} />{OUTCOME_SHORT[c.o]} <span className="font-mono text-ink-2">{c.n}</span></span>
        ))}
        {items.length > 0 && (
          <span className="ml-auto">
            <span className="font-mono text-ink-2">{formatPercent(sustained / items.length)}</span> kept burning
            {items.length < 20 && <span className="text-risk-elevated"> · small sample</span>}
          </span>
        )}
      </div>
    </div>
  );
}

export function ExperimentExplorer() {
  // Same cache key as Mission Control, so the list is fetched once per session.
  const list = useApi<ExperimentList>(`${endpoints.experiments}?limit=300`);
  const stats = useApi<StatsResponse>(endpoints.stats);
  const params = useSearchParams();

  const [filters, setFilters] = useState<ExperimentFilters>(DEFAULT_FILTERS);
  const [sort, setSort] = useState<Sort>({ key: "test_id", dir: "asc" });
  const [page, setPage] = useState(0);
  const [openId, setOpenId] = useState<number | null>(() => {
    const t = Number(params.get("test"));
    return Number.isInteger(t) && t > 0 ? t : null;
  });

  const all = list.data?.items;
  const filtered = useMemo(() => (all ? filterExperiments(all, filters) : []), [all, filters]);
  const sorted = useMemo(() => sortExperiments(filtered, sort), [filtered, sort]);
  const pages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const current = Math.min(page, pages - 1);
  const visible = sorted.slice(current * PAGE_SIZE, (current + 1) * PAGE_SIZE);
  const open = all?.find((e) => e.test_id === openId) ?? null;

  const changeFilters: Dispatch<SetStateAction<ExperimentFilters>> = (update) => { setFilters(update); setPage(0); };
  const changeSort = (key: SortKey) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: key === "risk" || key === "burn_time" ? "desc" : "asc" }));

  // Keep ?test= in the URL so a test can be linked; native history calls stay in sync with Next's router.
  const openTest = (id: number | null) => {
    setOpenId(id);
    const url = new URL(window.location.href);
    if (id === null) url.searchParams.delete("test");
    else url.searchParams.set("test", String(id));
    window.history.replaceState(null, "", url);
  };

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHeader
        eyebrow="Experiments"
        title="Experiment Explorer"
        subtitle="Every droplet test from NASA's Flame Extinguishment Experiment aboard the ISS, 2009–2011. Select a test to see what was measured and how the model scored it."
      />

      {list.error ? (
        <ErrorState message={list.error.message} onRetry={() => list.mutate()} />
      ) : !all ? (
        <Panel title="FLEX tests" provenance="observed"><LoadingState rows={10} label="Loading experiments" /></Panel>
      ) : (
        <Panel
          title="FLEX tests"
          provenance="observed"
          description={<>Showing <span className="font-mono text-ink-2">{filtered.length}</span> of {all.length} tests. Model Fire Risk is out-of-fold: each test was scored by models that never saw it.</>}
        >
          <div className="space-y-5">
            <ExperimentFiltersBar value={filters} onChange={changeFilters} />
            <OutcomeMix items={filtered} />

            {filtered.length === 0 ? (
              <EmptyState title="No tests match" icon={<SearchX className="size-5" aria-hidden="true" />}>
                Try removing a filter or searching for a different FLEX identifier.
              </EmptyState>
            ) : (
              <>
                <ExperimentTable items={visible} sort={sort} onSort={changeSort} onOpen={openTest} selected={openId} />
                <nav aria-label="Pages" className="flex items-center justify-between gap-3 text-xs text-ink-3">
                  <span>
                    {current * PAGE_SIZE + 1}–{Math.min((current + 1) * PAGE_SIZE, sorted.length)} of {sorted.length}
                  </span>
                  <span className="flex items-center gap-1">
                    <button type="button" disabled={current === 0} onClick={() => setPage(current - 1)} aria-label="Previous page"
                      className="rounded-lg p-1.5 transition hover:bg-white/[0.06] hover:text-ink disabled:opacity-30">
                      <ChevronLeft className="size-4" aria-hidden="true" />
                    </button>
                    <span className="font-mono text-ink-2">{current + 1} / {pages}</span>
                    <button type="button" disabled={current >= pages - 1} onClick={() => setPage(current + 1)} aria-label="Next page"
                      className="rounded-lg p-1.5 transition hover:bg-white/[0.06] hover:text-ink disabled:opacity-30">
                      <ChevronRight className="size-4" aria-hidden="true" />
                    </button>
                  </span>
                </nav>
              </>
            )}
          </div>
        </Panel>
      )}

      <ExperimentDrawer experiment={open} alert={stats.data?.model.alert_threshold_score ?? 18.4} onClose={() => openTest(null)} />
    </div>
  );
}
