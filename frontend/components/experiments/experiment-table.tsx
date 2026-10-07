"use client";

import { ArrowDown, ArrowUp, ArrowUpDown, ChevronRight, TriangleAlert } from "lucide-react";

import { OutcomeShape } from "@/components/charts/outcome-shape";
import { OUTCOME_SHORT, RISK_COLORS } from "@/lib/chart-theme";
import { cn } from "@/lib/cn";
import type { Sort, SortKey } from "@/lib/experiment-filters";
import { formatRisk } from "@/lib/format";
import type { ExperimentSummary } from "@/lib/types";

export const testLabel = (id: number) => `Test ${String(id).padStart(3, "0")}`;
export const formatDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(iso));
export const atmosphereText = (e: ExperimentSummary) =>
  `${e.oxygen_percent}% O₂${e.suppressant === "CO2" ? ` · ${e.co2_percent}% CO₂` : e.suppressant === "He" ? ` · ${e.he_percent}% He` : ""}`;
const pressureText = (e: ExperimentSummary) => (e.pressure_atm !== null ? `${e.pressure_atm.toFixed(2)} atm` : e.pressure_level.replace("atm", " atm"));

function RiskCell({ e }: { e: ExperimentSummary }) {
  if (!e.prediction) return <span className="text-xs text-ink-3" title="Outside the model's scope (pressure or missing droplet size)">not modelled</span>;
  const p = e.prediction;
  return (
    <span className="flex items-center gap-2" title={`${p.method}: Fire Risk ${p.fire_risk} (${p.risk_level})`}>
      <span className="h-1.5 w-12 overflow-hidden rounded-full bg-white/[0.07]" aria-hidden="true">
        <span className="block h-full rounded-full" style={{ width: `${p.fire_risk}%`, background: RISK_COLORS[p.risk_level] }} />
      </span>
      <span className="font-mono text-xs tabular-nums text-ink">{formatRisk(p.fire_risk)}</span>
    </span>
  );
}

function Outcome({ e }: { e: ExperimentSummary }) {
  return (
    <span className="flex items-center gap-1.5 text-xs text-ink-2">
      <OutcomeShape outcome={e.outcome} />{OUTCOME_SHORT[e.outcome]}
    </span>
  );
}

const COLUMNS: { key: string; label: string; sort?: SortKey; className?: string }[] = [
  { key: "test", label: "Test", sort: "test_id" },
  { key: "date", label: "Date (UTC)", sort: "date", className: "hidden xl:table-cell" },
  { key: "fuel", label: "Fuel" },
  { key: "atm", label: "Atmosphere", sort: "oxygen" },
  { key: "d0", label: "d₀", sort: "droplet" },
  { key: "p", label: "Pressure", className: "hidden lg:table-cell" },
  { key: "outcome", label: "Outcome" },
  { key: "burn", label: "Burn time", sort: "burn_time", className: "hidden lg:table-cell" },
  { key: "risk", label: "Model Fire Risk", sort: "risk" },
];

interface TableProps {
  items: ExperimentSummary[];
  sort: Sort;
  onSort: (key: SortKey) => void;
  onOpen: (id: number) => void;
  selected: number | null;
}

/** Observed FLEX tests: a sortable table on wide screens, a card list on phones. Rows open the detail drawer. */
export function ExperimentTable({ items, sort, onSort, onOpen, selected }: TableProps) {
  return (
    <>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">NASA FLEX tests. Column headers sort the table; select a test to see its details.</caption>
          <thead>
            <tr className="border-b border-white/[0.07]">
              {COLUMNS.map((c) => {
                const active = c.sort && sort.key === c.sort;
                const Icon = active ? (sort.dir === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
                return (
                  <th key={c.key} scope="col" className={cn("whitespace-nowrap px-3 py-2.5 font-normal", c.className)}
                    aria-sort={active ? (sort.dir === "asc" ? "ascending" : "descending") : undefined}>
                    {c.sort ? (
                      <button type="button" onClick={() => onSort(c.sort as SortKey)}
                        className={cn("label-caps inline-flex items-center gap-1 text-[0.625rem] transition hover:text-ink", active && "text-flame")}>
                        {c.label}<Icon className="size-3" aria-hidden="true" />
                      </button>
                    ) : (
                      <span className="label-caps text-[0.625rem]">{c.label}</span>
                    )}
                  </th>
                );
              })}
              <th scope="col" className="w-8"><span className="sr-only">Open</span></th>
            </tr>
          </thead>
          <tbody>
            {items.map((e) => (
              <tr
                key={e.test_id}
                onClick={() => onOpen(e.test_id)}
                className={cn(
                  "cursor-pointer border-b border-white/[0.04] transition-colors hover:bg-white/[0.035]",
                  selected === e.test_id && "bg-flame/[0.06]",
                  !e.in_model_scope && "text-ink-3",
                )}
              >
                <td className="whitespace-nowrap px-3 py-2.5">
                  <button type="button" onClick={(ev) => { ev.stopPropagation(); onOpen(e.test_id); }}
                    className="text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-flame/60 rounded">
                    <span className="block font-mono text-xs font-semibold text-ink">{String(e.test_id).padStart(3, "0")}</span>
                    <span className="block font-mono text-[0.6875rem] text-ink-3">{e.flex_identifier}</span>
                  </button>
                </td>
                <td className="hidden whitespace-nowrap px-3 py-2.5 text-xs text-ink-3 xl:table-cell">{formatDate(e.datetime_gmt)}</td>
                <td className="px-3 py-2.5 text-xs text-ink-2">{e.fuel === "Heptane" ? "n-Heptane" : "Methanol"}</td>
                <td className="whitespace-nowrap px-3 py-2.5 text-xs text-ink-2">{atmosphereText(e)}</td>
                <td className="whitespace-nowrap px-3 py-2.5 font-mono text-xs text-ink-2">{e.droplet_diameter_mm !== null ? `${e.droplet_diameter_mm.toFixed(2)} mm` : "—"}</td>
                <td className="hidden whitespace-nowrap px-3 py-2.5 font-mono text-xs text-ink-3 lg:table-cell">{pressureText(e)}</td>
                <td className="whitespace-nowrap px-3 py-2.5"><Outcome e={e} /></td>
                <td className="hidden whitespace-nowrap px-3 py-2.5 font-mono text-xs text-ink-2 lg:table-cell">{e.burn_time_s !== null ? `${e.burn_time_s.toFixed(1)} s` : "—"}</td>
                <td className="whitespace-nowrap px-3 py-2.5"><RiskCell e={e} /></td>
                <td className="px-2 py-2.5 text-ink-3">
                  <span className="flex items-center gap-1">
                    {e.qc_flags.length > 0 && <TriangleAlert className="size-3.5 text-risk-elevated/80" aria-label="Has data-quality notes" />}
                    <ChevronRight className="size-4" aria-hidden="true" />
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* phones: cards */}
      <ul className="space-y-2 md:hidden">
        {items.map((e) => (
          <li key={e.test_id}>
            <button type="button" onClick={() => onOpen(e.test_id)}
              className={cn("w-full rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5 text-left transition hover:bg-white/[0.04]",
                selected === e.test_id && "border-flame/30")}>
              <span className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-semibold text-ink">{testLabel(e.test_id)} · <span className="text-ink-3">{e.flex_identifier}</span></span>
                <Outcome e={e} />
              </span>
              <span className="mt-1.5 block text-xs text-ink-2">
                {e.fuel === "Heptane" ? "n-Heptane" : "Methanol"} · {atmosphereText(e)} · {e.droplet_diameter_mm !== null ? `${e.droplet_diameter_mm} mm` : "d₀ —"}
              </span>
              <span className="mt-2 flex items-center justify-between gap-2">
                <RiskCell e={e} />
                {e.qc_flags.length > 0 && <TriangleAlert className="size-3.5 text-risk-elevated/80" aria-label="Has data-quality notes" />}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}
