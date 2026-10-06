"use client";

import { Ellipsis, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { cn } from "@/lib/cn";
import { NAV_ITEMS } from "@/lib/nav";

/** Mobile: bottom tab bar with the four primary pages plus a "More" sheet listing the rest. */
export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const primary = NAV_ITEMS.filter((i) => i.primary);
  const rest = NAV_ITEMS.filter((i) => !i.primary);
  const moreActive = rest.some((i) => i.href === pathname);

  return (
    <>
      <nav
        aria-label="Main"
        className="fixed inset-x-0 bottom-0 z-40 border-t border-white/[0.08] bg-space-900/90 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl md:hidden"
      >
        <ul className="grid grid-cols-5">
          {primary.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn("flex flex-col items-center gap-1 py-2.5 text-[0.625rem] font-medium", active ? "text-flame" : "text-ink-3")}
                >
                  <Icon className="size-5" aria-hidden="true" />
                  {item.label.split(" ")[0]}
                </Link>
              </li>
            );
          })}
          <li>
            <button
              type="button"
              onClick={() => setOpen(true)}
              aria-expanded={open}
              aria-controls="mobile-more"
              className={cn("flex w-full flex-col items-center gap-1 py-2.5 text-[0.625rem] font-medium", moreActive ? "text-flame" : "text-ink-3")}
            >
              <Ellipsis className="size-5" aria-hidden="true" />
              More
            </button>
          </li>
        </ul>
      </nav>

      <AnimatePresence>
        {open && (
          <>
            <motion.div
              className="fixed inset-0 z-50 bg-black/60 md:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <motion.div
              id="mobile-more"
              role="dialog"
              aria-modal="true"
              aria-label="More pages"
              className="fixed inset-x-0 bottom-0 z-50 rounded-t-3xl border-t border-white/10 bg-space-800 p-5 pb-[calc(env(safe-area-inset-bottom)+1.25rem)] md:hidden"
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", stiffness: 340, damping: 34 }}
            >
              <div className="mb-4 flex items-center justify-between">
                <p className="label-caps">More</p>
                <button type="button" onClick={() => setOpen(false)} aria-label="Close" className="rounded-lg p-1.5 text-ink-2 hover:bg-white/[0.06]">
                  <X className="size-5" aria-hidden="true" />
                </button>
              </div>
              <ul className="grid grid-cols-2 gap-2">
                {rest.map((item) => {
                  const Icon = item.icon;
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={() => setOpen(false)}
                        className={cn(
                          "flex items-center gap-2.5 rounded-xl border px-3 py-3 text-sm",
                          pathname === item.href ? "border-flame/30 bg-flame/10 text-ink" : "border-white/[0.06] bg-white/[0.02] text-ink-2",
                        )}
                      >
                        <Icon className="size-4 text-flame" aria-hidden="true" />
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
