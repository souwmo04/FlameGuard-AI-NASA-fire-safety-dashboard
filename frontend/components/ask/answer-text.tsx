"use client";

import { Fragment, type ReactNode } from "react";

import { cn } from "@/lib/cn";

/**
 * Renders the model's answer as plain React elements (never as HTML): paragraphs, "-"/"1." lists,
 * **bold**, and [n] citations as buttons that jump to the cited passage. Unknown numbers stay as text.
 */
function inline(text: string, valid: Set<number>, onCite: (n: number) => void, active: number | null): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /\*\*([^*]+)\*\*|\[(\d+)\]/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    if (m[1] !== undefined) {
      out.push(<strong key={i++} className="font-semibold text-ink">{m[1]}</strong>);
    } else {
      const n = Number(m[2]);
      out.push(valid.has(n) ? (
        <button key={i++} type="button" onClick={() => onCite(n)} aria-label={`Show source ${n}`}
          className={cn("mx-0.5 inline-flex h-5 min-w-5 -translate-y-px items-center justify-center rounded-md border px-1 align-middle font-mono text-[0.6875rem] font-semibold transition",
            active === n ? "border-flame/60 bg-flame/20 text-flame" : "border-plasma/30 bg-plasma/10 text-plasma hover:bg-plasma/20")}>
          {n}
        </button>
      ) : (
        <span key={i++} className="font-mono text-xs text-ink-3">[{n}]</span>
      ));
    }
    last = re.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export function AnswerText({ text, valid, onCite, active, streaming }: {
  text: string;
  valid: Set<number>;
  onCite: (n: number) => void;
  active: number | null;
  streaming?: boolean;
}) {
  const blocks: { type: "p" | "ul" | "ol"; lines: string[] }[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) {
      blocks.push({ type: "p", lines: [] });
      continue;
    }
    const bullet = /^[-*•]\s+(.*)/.exec(line);
    const number = /^\d+[.)]\s+(.*)/.exec(line);
    const type = bullet ? "ul" : number ? "ol" : "p";
    const content = bullet?.[1] ?? number?.[1] ?? line;
    const prev = blocks[blocks.length - 1];
    if (prev && prev.type === type && (type !== "p" || prev.lines.length > 0)) prev.lines.push(content);
    else blocks.push({ type, lines: [content] });
  }
  const shown = blocks.filter((b) => b.lines.length > 0);

  return (
    <div className="space-y-3 text-[0.9375rem] leading-relaxed text-ink-2">
      {shown.map((b, bi) => {
        const last = bi === shown.length - 1;
        const cursor = streaming && last ? <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-flame align-middle" aria-hidden="true" /> : null;
        if (b.type === "p") {
          return <p key={bi}>{inline(b.lines.join(" "), valid, onCite, active)}{cursor}</p>;
        }
        const List = b.type === "ul" ? "ul" : "ol";
        return (
          <List key={bi} className={cn("space-y-1.5 pl-5", b.type === "ul" ? "list-disc marker:text-flame" : "list-decimal marker:text-ink-3")}>
            {b.lines.map((l, li) => (
              <li key={li}>{inline(l, valid, onCite, active)}{li === b.lines.length - 1 ? cursor : null}</li>
            ))}
          </List>
        );
      })}
      {shown.length === 0 && streaming && <Fragment>{<span className="inline-block h-4 w-1.5 animate-pulse rounded-sm bg-flame" aria-hidden="true" />}</Fragment>}
    </div>
  );
}
