import type { ReactNode } from "react";

import { MobileNav } from "./mobile-nav";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

/** Platform frame: sidebar (md+), top bar, scrollable content, mobile bottom navigation. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-dvh">
      <div aria-hidden="true" className="grid-backdrop pointer-events-none fixed inset-0 -z-10" />
      <div aria-hidden="true" className="pointer-events-none fixed -top-40 left-1/3 -z-10 size-[36rem] rounded-full bg-flame/[0.05] blur-3xl" />
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-4 pb-28 pt-6 sm:px-6 md:pb-12 lg:px-10 lg:pt-10">
          {children}
        </main>
      </div>
      <MobileNav />
    </div>
  );
}
