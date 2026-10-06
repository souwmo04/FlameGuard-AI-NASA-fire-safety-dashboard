"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";
import { NAV_GROUPS, NAV_ITEMS } from "@/lib/nav";

import { Brand } from "./brand";

/**
 * Desktop (lg+): full sidebar with labels. Tablet (md-lg): icon rail; labels are available
 * as accessible names and tooltips. Hidden on mobile, which uses the bottom bar instead.
 */
export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sticky top-0 hidden h-dvh shrink-0 flex-col border-r border-white/[0.06] bg-space-900/70 backdrop-blur-xl md:flex md:w-[76px] lg:w-64">
      <div className="flex h-16 items-center px-5 lg:px-6">
        <span className="lg:hidden"><Brand collapsed /></span>
        <span className="hidden lg:block"><Brand /></span>
      </div>
      <nav aria-label="Main" className="flex-1 overflow-y-auto px-3 pb-6">
        {NAV_GROUPS.map((group) => (
          <div key={group} className="mt-5 first:mt-2">
            <p className="label-caps mb-2 hidden px-3 lg:block">{group}</p>
            <ul className="space-y-1">
              {NAV_ITEMS.filter((i) => i.group === group).map((item) => {
                const active = pathname === item.href;
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      aria-current={active ? "page" : undefined}
                      aria-label={item.label}
                      title={item.label}
                      className={cn(
                        "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition md:justify-center lg:justify-start",
                        active ? "text-ink" : "text-ink-2 hover:bg-white/[0.04] hover:text-ink",
                      )}
                    >
                      {active && (
                        <motion.span
                          layoutId="sidebar-active"
                          className="absolute inset-0 rounded-xl border border-flame/25 bg-gradient-to-r from-flame/[0.14] to-transparent"
                          transition={{ type: "spring", stiffness: 380, damping: 32 }}
                        />
                      )}
                      <Icon className={cn("relative size-[18px] shrink-0", active ? "text-flame" : "text-ink-3 group-hover:text-ink-2")} aria-hidden="true" />
                      <span className="relative hidden lg:inline">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
      <div className="hidden border-t border-white/[0.06] p-4 text-[0.6875rem] leading-relaxed text-ink-3 lg:block">
        Data: NASA FLEX (PSI-69), ISS 2009–2011. Research prototype — not a certified fire-safety system.
      </div>
    </aside>
  );
}
