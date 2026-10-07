import { ArrowRight, Brain, BrainCircuit, Earth, FlaskConical, Gauge, GitCompareArrows, Radar, SlidersHorizontal } from "lucide-react";
import Link from "next/link";

import { Brand } from "@/components/layout/brand";
import { CommandPaletteTrigger } from "@/components/layout/command-palette";
import { FlameOrb } from "@/components/landing/flame-orb";
import { HeroStats } from "@/components/landing/hero-stats";
import { Starfield } from "@/components/landing/starfield";
import { ButtonLink } from "@/components/ui/button-link";
import { GlassCard } from "@/components/ui/glass-card";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { PROVENANCE } from "@/lib/provenance";
import type { Provenance } from "@/lib/types";

const CAPABILITIES = [
  { icon: FlaskConical, title: "NASA evidence", text: "Every ISS test from the Flame Extinguishment Experiment, cleaned without inventing a single value.", href: "/experiments" },
  { icon: Brain, title: "Calibrated risk", text: "A model validated on tests it never saw, with risk bands tied to how often flames really kept burning.", href: "/risk" },
  { icon: Gauge, title: "Explainable", text: "Each prediction decomposed into what pushed the risk up or down — and flagged when it is an extrapolation.", href: "/risk" },
  { icon: SlidersHorizontal, title: "What-if lab", text: "Change oxygen, suppressant or droplet size and watch the predicted behaviour respond, step by step.", href: "/what-if" },
  { icon: GitCompareArrows, title: "Suppressant lab", text: "Nitrogen, CO₂ and helium compared on observed tests only — with an honest verdict when the data cannot rank them.", href: "/suppressants" },
  { icon: Radar, title: "Similar tests", text: "Describe a droplet and see the closest real ISS tests and what actually happened to them.", href: "/similar" },
  { icon: BrainCircuit, title: "Ask FlameGuard", text: "Questions answered from NASA's FLEX report and the project's documents, with every claim cited.", href: "/knowledge" },
  { icon: Earth, title: "The science", text: "Why flames behave differently in microgravity, explained with page-level links to the NASA report.", href: "/science" },
];

const LEGEND: Provenance[] = ["observed", "prediction", "estimate", "explanation", "interpretation", "hypothetical"];

export default function LandingPage() {
  return (
    <div className="relative overflow-hidden">
      <Starfield className="pointer-events-none absolute inset-0 -z-10 h-[110dvh] w-full" />
      <div aria-hidden="true" className="pointer-events-none absolute -top-48 right-[-10%] -z-10 size-[44rem] rounded-full bg-plasma/[0.06] blur-3xl" />
      <div aria-hidden="true" className="pointer-events-none absolute top-[30%] left-[-15%] -z-10 size-[38rem] rounded-full bg-flame/[0.07] blur-3xl" />

      <header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <Brand />
        <div className="flex items-center gap-3">
          <CommandPaletteTrigger />
          <Link href="/dashboard" className="hidden text-sm text-ink-2 transition hover:text-ink sm:inline">
            Mission Control
          </Link>
        </div>
      </header>

      <main id="main">
        {/* hero */}
        <section className="mx-auto grid max-w-7xl items-center gap-10 px-5 pb-16 pt-8 sm:px-8 lg:grid-cols-[1.15fr_1fr] lg:pb-24 lg:pt-16">
          <div className="space-y-7">
            <p className="label-caps !text-plasma">NASA Space Apps Challenge 2026 · Flame in Freefall</p>
            <h1 className="font-display text-5xl font-bold leading-[0.95] tracking-tight sm:text-7xl">
              FLAMEGUARD <span className="text-gradient-flame">AI</span>
            </h1>
            <p className="font-display text-lg font-medium uppercase tracking-[0.16em] text-ink sm:text-xl">
              AI-powered fire safety intelligence
              <br className="hidden sm:block" /> for space exploration
            </p>
            <p className="max-w-xl text-base text-ink-2 sm:text-lg">
              Transforming decades of NASA microgravity combustion experiments into actionable fire-safety insights.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <ButtonLink href="/experiments" variant="secondary">
                Explore NASA data
              </ButtonLink>
              <ButtonLink href="/risk">
                Run fire risk analysis <ArrowRight className="size-4" aria-hidden="true" />
              </ButtonLink>
            </div>
          </div>

          <figure className="mx-auto w-full max-w-md lg:max-w-none">
            <FlameOrb className="mx-auto w-full max-w-[30rem]" />
            <figcaption className="mx-auto mt-2 max-w-sm text-center text-xs leading-relaxed text-ink-3">
              In space, fuels burn as rounded balls of flame rather than the upward-pointing cones seen on Earth.
              <span className="block text-ink-3/80">— NASA, BASS-II investigation description (PSI-25)</span>
            </figcaption>
          </figure>
        </section>

        {/* live statistics */}
        <section aria-labelledby="stats-heading" className="mx-auto max-w-7xl px-5 pb-20 sm:px-8">
          <h2 id="stats-heading" className="label-caps mb-4">Live from the FlameGuard API</h2>
          <HeroStats />
        </section>

        {/* capabilities */}
        <section aria-labelledby="cap-heading" className="mx-auto max-w-7xl px-5 pb-20 sm:px-8">
          <h2 id="cap-heading" className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
            From ISS experiments to explainable fire-safety insight
          </h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {CAPABILITIES.map(({ icon: Icon, title, text, href }) => (
              <Link key={title} href={href} className="group">
                <GlassCard className="h-full p-5 transition group-hover:border-flame/30">
                  <Icon className="size-5 text-flame" aria-hidden="true" />
                  <h3 className="mt-4 font-display text-lg font-semibold">{title}</h3>
                  <p className="mt-2 text-sm text-ink-2">{text}</p>
                </GlassCard>
              </Link>
            ))}
          </div>
        </section>

        {/* provenance promise */}
        <section aria-labelledby="prov-heading" className="mx-auto max-w-7xl px-5 pb-24 sm:px-8">
          <GlassCard glow className="p-6 sm:p-10">
            <h2 id="prov-heading" className="font-display text-2xl font-semibold tracking-tight">
              Every number tells you what it is
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-ink-2">
              A NASA measurement, a model prediction and a hypothetical scenario never look alike. Each value carries one of
              these labels.
            </p>
            <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {LEGEND.map((kind) => (
                <li key={kind} className="flex flex-col items-start gap-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                  <ProvenanceBadge kind={kind} />
                  <p className="text-sm text-ink-2">{PROVENANCE[kind].description}</p>
                </li>
              ))}
            </ul>
          </GlassCard>
        </section>
      </main>

      <footer className="border-t border-white/[0.06]">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-8 text-xs text-ink-3 sm:px-8 md:flex-row md:justify-between">
          <p>
            Data: NASA Physical Sciences Informatics, FLEX (PSI-69), DOI{" "}
            <a className="text-plasma hover:underline" href="https://doi.org/10.60555/mbq8-0451">10.60555/mbq8-0451</a>, CC0-1.0.
          </p>
          <p>Research prototype for NASA Space Apps 2026 — not a certified spacecraft fire-safety system.</p>
        </div>
      </footer>
    </div>
  );
}
