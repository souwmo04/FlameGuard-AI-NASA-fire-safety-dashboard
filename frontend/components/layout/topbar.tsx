"use client";

import { usePathname } from "next/navigation";

import { StatusPill } from "@/components/ui/status-pill";
import { NAV_ITEMS } from "@/lib/nav";

import { Brand } from "./brand";
import { CommandPaletteTrigger } from "./command-palette";

export function Topbar() {
  const pathname = usePathname();
  const current = NAV_ITEMS.find((i) => i.href === pathname);
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-white/[0.06] bg-space-950/70 px-4 backdrop-blur-xl sm:px-6">
      <span className="md:hidden"><Brand collapsed /></span>
      <p className="hidden font-mono text-xs uppercase tracking-[0.18em] text-ink-3 md:block">
        FlameGuard <span className="text-ink-3/60">/</span> <span className="text-ink-2">{current?.label ?? "Platform"}</span>
      </p>
      <div className="ml-auto flex items-center gap-2">
        <CommandPaletteTrigger />
        <StatusPill />
      </div>
    </header>
  );
}
