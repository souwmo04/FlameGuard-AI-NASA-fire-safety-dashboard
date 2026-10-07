"use client";

import { BookOpen, Database, ExternalLink, FileText, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { cn } from "@/lib/cn";
import type { Passage } from "@/lib/types";

export const PASSAGE_KIND: Record<Passage["kind"], { label: string; icon: LucideIcon; tone: string }> = {
  nasa: { label: "NASA report", icon: BookOpen, tone: "text-prov-observed border-prov-observed/30 bg-prov-observed/10" },
  project: { label: "FlameGuard docs", icon: FileText, tone: "text-prov-estimate border-prov-estimate/30 bg-prov-estimate/10" },
  live: { label: "Live data", icon: Database, tone: "text-prov-evaluation border-prov-evaluation/30 bg-prov-evaluation/10" },
};

/** One numbered source passage; long text collapses. Cited passages are emphasised. */
export function PassageCard({ passage: p, id, cited, active }: { passage: Passage; id: string; cited: boolean; active: boolean }) {
  const [open, setOpen] = useState(false);
  const kind = PASSAGE_KIND[p.kind];
  const Icon = kind.icon;
  const external = p.url.startsWith("http");
  const long = p.text.length > 260;
  const linkClass = "inline-flex items-center gap-1 text-xs text-plasma hover:underline";
  return (
    <li id={id} className={cn("scroll-mt-24 rounded-xl border p-3.5 transition-colors duration-500",
      active ? "border-flame/50 bg-flame/[0.07]" : cited ? "border-white/[0.1] bg-white/[0.03]" : "border-white/[0.05] bg-white/[0.015] opacity-80")}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={cn("inline-flex size-6 items-center justify-center rounded-md font-mono text-xs font-bold",
          cited ? "bg-plasma/15 text-plasma" : "bg-white/[0.06] text-ink-3")}>{p.n}</span>
        <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[0.625rem] font-semibold uppercase tracking-[0.12em]", kind.tone)}>
          <Icon className="size-3" aria-hidden="true" />{kind.label}
        </span>
        <span className="font-mono text-xs text-ink-2">{p.location}</span>
        {!cited && <span className="text-[0.6875rem] text-ink-3">not cited</span>}
      </div>
      <p className="mt-2 text-xs font-medium text-ink">{p.section !== p.location ? p.section : p.source_title}</p>
      <p className={cn("mt-1 text-xs leading-relaxed text-ink-3", !open && long && "line-clamp-3")}>{p.text}</p>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        {long && (
          <button type="button" onClick={() => setOpen((o) => !o)} className="text-xs text-ink-2 hover:text-ink" aria-expanded={open}>
            {open ? "Show less" : "Show full passage"}
          </button>
        )}
        {external ? (
          <a href={p.url} target="_blank" rel="noreferrer" className={linkClass}>
            Open source<ExternalLink className="size-3" aria-hidden="true" />
          </a>
        ) : (
          <Link href={p.url} className={linkClass}>Open in FlameGuard</Link>
        )}
      </div>
    </li>
  );
}
