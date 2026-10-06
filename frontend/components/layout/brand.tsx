import Link from "next/link";

import { cn } from "@/lib/cn";

/** FlameGuard mark: a spherical microgravity flame (blue core, amber halo) inside an orbit. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={cn("size-8", className)} aria-hidden="true">
      <defs>
        <radialGradient id="fg-core" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#e0f2fe" />
          <stop offset="35%" stopColor="#38bdf8" />
          <stop offset="70%" stopColor="#f59e0b" />
          <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
        </radialGradient>
      </defs>
      <ellipse cx="16" cy="16" rx="14" ry="6.5" fill="none" stroke="#22d3ee" strokeOpacity="0.55" strokeWidth="1" transform="rotate(-24 16 16)" />
      <circle cx="16" cy="16" r="8" fill="url(#fg-core)" />
      <circle cx="27.5" cy="10.6" r="1.4" fill="#fbbf24" />
    </svg>
  );
}

export function Brand({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <Link href="/" className="flex items-center gap-2.5" aria-label="FlameGuard AI home">
      <BrandMark />
      {!collapsed && (
        <span className="font-display text-base font-semibold tracking-tight text-ink">
          FlameGuard <span className="text-gradient-flame">AI</span>
        </span>
      )}
    </Link>
  );
}
