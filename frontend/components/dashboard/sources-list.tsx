import { Database, ExternalLink, FileText } from "lucide-react";

import type { Source } from "@/lib/types";

/** NASA sources behind every value, with DOI / report links. */
export function SourcesList({ sources }: { sources: Source[] }) {
  return (
    <ul className="space-y-3">
      {sources.map((s) => {
        const Icon = s.kind === "dataset" ? Database : FileText;
        return (
          <li key={s.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5">
            <div className="flex items-start gap-3">
              <Icon className="mt-0.5 size-4 shrink-0 text-plasma" aria-hidden="true" />
              <div className="min-w-0 space-y-1">
                <a href={s.url} target="_blank" rel="noreferrer" className="group inline-flex items-start gap-1 text-sm font-medium text-ink hover:text-plasma">
                  {s.title}
                  <ExternalLink className="mt-1 size-3 shrink-0 opacity-60 group-hover:opacity-100" aria-hidden="true" />
                  <span className="sr-only">(opens in a new tab)</span>
                </a>
                <p className="text-xs text-ink-3">
                  {s.publisher}
                  {s.doi && <> · DOI <span className="font-mono text-ink-2">{s.doi}</span></>}
                  {s.license && <> · {s.license}</>}
                </p>
                <p className="text-xs text-ink-3">{s.used_for}</p>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
