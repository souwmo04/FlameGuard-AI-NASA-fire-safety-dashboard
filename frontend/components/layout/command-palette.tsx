"use client";

import { ArrowRight, Command, Search } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { cn } from "@/lib/cn";
import { NAV_ITEMS } from "@/lib/nav";

interface PaletteContextValue {
  open: () => void;
}

const PaletteContext = createContext<PaletteContextValue>({ open: () => {} });
export const useCommandPalette = () => useContext(PaletteContext);

const COMMANDS = NAV_ITEMS.map((item) => ({
  id: item.href,
  label: item.href === "/risk" ? "Go to Fire Risk" : item.href === "/experiments" ? "Open Experiment Explorer"
    : item.href === "/knowledge" ? "Ask FlameGuard" : `Open ${item.label}`,
  description: item.description,
  href: item.href,
  icon: item.icon,
  keywords: `${item.label} ${item.description}`.toLowerCase(),
}));

/** Ctrl/Cmd+K command palette for jumping between pages. Accessible dialog with keyboard navigation. */
export function CommandPaletteProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const restoreFocus = useRef<HTMLElement | null>(null);

  const open = useCallback(() => {
    restoreFocus.current = document.activeElement as HTMLElement | null;
    setQuery("");
    setActive(0);
    setIsOpen(true);
  }, []);
  const close = useCallback(() => {
    setIsOpen(false);
    restoreFocus.current?.focus?.();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) close();
        else open();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, open, close]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? COMMANDS.filter((c) => c.keywords.includes(q) || c.label.toLowerCase().includes(q)) : COMMANDS;
  }, [query]);

  const run = (index: number) => {
    const cmd = results[index];
    if (!cmd) return;
    setIsOpen(false);
    router.push(cmd.href);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      close();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => (results.length ? (a + 1) % results.length : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => (results.length ? (a - 1 + results.length) % results.length : 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      run(active);
    }
  };

  return (
    <PaletteContext.Provider value={{ open }}>
      {children}
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-[60] flex items-start justify-center px-4 pt-[14vh]">
            <motion.div
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={close}
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label="Command palette"
              onKeyDown={onKeyDown}
              className="glass relative w-full max-w-xl overflow-hidden rounded-2xl bg-space-800/95"
              initial={{ opacity: 0, scale: 0.97, y: -8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.97, y: -8 }}
              transition={{ duration: 0.16 }}
            >
              <div className="flex items-center gap-3 border-b border-white/[0.08] px-4">
                <Search className="size-4 text-ink-3" aria-hidden="true" />
                <input
                  ref={inputRef}
                  autoFocus
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setActive(0);
                  }}
                  placeholder="Jump to a page…"
                  aria-label="Search commands"
                  aria-controls="palette-results"
                  aria-activedescendant={results[active] ? `cmd-${active}` : undefined}
                  className="h-14 flex-1 bg-transparent text-sm text-ink placeholder:text-ink-3 focus:outline-none"
                />
                <kbd className="rounded border border-white/10 px-1.5 py-0.5 font-mono text-[0.625rem] text-ink-3">ESC</kbd>
              </div>
              <ul id="palette-results" role="listbox" className="max-h-80 overflow-y-auto p-2">
                {results.length === 0 && <li className="px-3 py-6 text-center text-sm text-ink-3">No matching command</li>}
                {results.map((cmd, i) => {
                  const Icon = cmd.icon;
                  return (
                    <li
                      key={cmd.id}
                      id={`cmd-${i}`}
                      role="option"
                      aria-selected={i === active}
                      onMouseEnter={() => setActive(i)}
                      onClick={() => run(i)}
                      className={cn(
                        "flex cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5",
                        i === active ? "bg-flame/10 text-ink" : "text-ink-2",
                      )}
                    >
                      <Icon className={cn("size-4", i === active ? "text-flame" : "text-ink-3")} aria-hidden="true" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">{cmd.label}</p>
                        <p className="truncate text-xs text-ink-3">{cmd.description}</p>
                      </div>
                      {i === active && <ArrowRight className="size-4 text-flame" aria-hidden="true" />}
                    </li>
                  );
                })}
              </ul>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </PaletteContext.Provider>
  );
}

/** Small button that opens the palette, showing the shortcut. */
export function CommandPaletteTrigger({ className }: { className?: string }) {
  const { open } = useCommandPalette();
  return (
    <button
      type="button"
      onClick={open}
      aria-label="Open command palette (Ctrl+K)"
      className={cn(
        "inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs text-ink-3 transition hover:border-white/20 hover:text-ink-2",
        className,
      )}
    >
      <Search className="size-3.5" aria-hidden="true" />
      <span className="hidden sm:inline">Search</span>
      <kbd className="inline-flex items-center gap-0.5 rounded border border-white/10 px-1 font-mono text-[0.625rem]">
        <Command className="size-2.5" aria-hidden="true" />K
      </kbd>
    </button>
  );
}
