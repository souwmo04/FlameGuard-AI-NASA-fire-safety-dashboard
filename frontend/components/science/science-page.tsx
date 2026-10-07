"use client";

import { ArrowRight, BookOpen, CircleAlert, Gauge, Microscope, Orbit, Ruler, ShieldAlert, Timer } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import Link from "next/link";
import { useState, type ReactNode } from "react";

import { OutcomeShape } from "@/components/charts/outcome-shape";
import { GlassCard } from "@/components/ui/glass-card";
import { PageHeader } from "@/components/ui/page-header";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { useApi } from "@/hooks/use-api";
import { endpoints } from "@/lib/api";
import { OUTCOME_LABEL } from "@/lib/chart-theme";
import { cn } from "@/lib/cn";
import type { StatsResponse } from "@/lib/types";

import { ApparatusDiagram } from "./apparatus-diagram";
import { Cite, REPORT } from "./cite";
import { GravityFlame } from "./gravity-flame";

function Section({ id, eyebrow, title, icon: Icon, children }: { id: string; eyebrow: string; title: string; icon: typeof Orbit; children: ReactNode }) {
  return (
    <motion.section id={id} aria-labelledby={`${id}-title`} className="scroll-mt-24 space-y-5"
      initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}>
      <div className="flex items-center gap-3">
        <span className="inline-flex size-9 items-center justify-center rounded-xl border border-flame/25 bg-flame/10 text-flame"><Icon className="size-4.5" aria-hidden="true" /></span>
        <div>
          <p className="label-caps text-[0.625rem] text-flame">{eyebrow}</p>
          <h2 id={`${id}-title`} className="font-display text-xl font-semibold tracking-tight text-ink sm:text-2xl">{title}</h2>
        </div>
      </div>
      {children}
    </motion.section>
  );
}

const P = ({ children }: { children: ReactNode }) => <p className="text-[0.9375rem] leading-relaxed text-ink-2">{children}</p>;

const STEPS = [
  { title: "Dispense", body: <>The operator slowly pushes fuel out between the two touching needles to form a droplet of the chosen size.<Cite p={5} /></> },
  { title: "Stretch", body: <>The needles move apart to just short of the distance at which the fuel would pull off one of them.<Cite p={5} /></> },
  { title: "Deploy", body: <>Recording starts and the needles retract rapidly and simultaneously, ideally leaving a motionless droplet.<Cite p={4} /><Cite p={5} /></> },
  { title: "Ignite", body: <>Hot-wire igniters close to the droplet are switched on for a preset time and power.<Cite p={5} /></> },
  { title: "Retract", body: <>The igniters switch off and pull back a relatively large distance from the droplet.<Cite p={5} /></> },
  { title: "Record", body: <>The cameras record for a preset time, typically about 40 s. A circulation fan then mixes the chamber gas before the next test in the same atmosphere.<Cite p={5} /></> },
];

function TestSequence() {
  const [step, setStep] = useState(0);
  const reduce = useReducedMotion();
  return (
    <div className="space-y-4">
      <ol className="grid grid-cols-3 gap-2 sm:grid-cols-6" aria-label="Test sequence">
        {STEPS.map((s, i) => (
          <li key={s.title}>
            <button type="button" onClick={() => setStep(i)} aria-current={step === i ? "step" : undefined}
              className={cn("relative w-full overflow-hidden rounded-xl border px-2 py-2.5 text-left transition",
                step === i ? "border-flame/40 bg-flame/[0.08]" : "border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04]")}>
              <span className={cn("block font-mono text-[0.625rem]", step >= i ? "text-flame" : "text-ink-3")}>{String(i + 1).padStart(2, "0")}</span>
              <span className={cn("block text-sm font-medium", step === i ? "text-ink" : "text-ink-2")}>{s.title}</span>
              {step === i && <motion.span layoutId="seq-bar" className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-flame to-ember" transition={reduce ? { duration: 0 } : undefined} />}
            </button>
          </li>
        ))}
      </ol>
      <motion.div key={step} initial={reduce ? false : { opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4" aria-live="polite">
        <p className="text-sm leading-relaxed text-ink-2"><span className="font-semibold text-ink">{STEPS[step].title}. </span>{STEPS[step].body}</p>
      </motion.div>
      <p className="text-xs text-ink-3">Each test is commanded remotely from the Telescience Support Center at NASA Glenn; the crew changes fuel canisters and gas bottles.<Cite p={1} /></p>
    </div>
  );
}

function Uncertainty() {
  const rows = [
    { label: "Droplet diameter (backlit camera)", um: 50, p: 8 },
    { label: "Flame diameter (UV / OH camera)", um: 200, p: 9 },
    { label: "Flame diameter (colour camera)", um: 250, p: 9 },
  ];
  return (
    <ul className="space-y-3">
      {rows.map((r, i) => (
        <li key={r.label} className="space-y-1.5">
          <div className="flex items-baseline justify-between gap-3 text-sm">
            <span className="text-ink-2">{r.label}<Cite p={r.p} /></span>
            <span className="font-mono text-ink">±{r.um} µm</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]" aria-hidden="true">
            <motion.div className="h-full rounded-full bg-gradient-to-r from-plasma/60 to-plasma" initial={{ width: 0 }} whileInView={{ width: `${(r.um / 250) * 100}%` }}
              viewport={{ once: true }} transition={{ duration: 0.8, delay: i * 0.1 }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function SciencePage() {
  const stats = useApi<StatsResponse>(endpoints.stats);
  const e = stats.data?.experiments;
  const outcomes = [
    { key: "Extinction" as const, n: e?.extinction, body: <>The flame goes out while fuel remains, leaving a measurable extinction diameter. NASA documented radiative extinction (at larger droplet sizes) and diffusive extinction (at smaller ones).<Cite p={2} /><Cite p={17} /></> },
    { key: "Completion" as const, n: e?.completion, body: <>The droplet burns until the fuel is used up, so no extinction diameter exists.<Cite p={19} /></> },
    { key: "Disruption" as const, n: e?.disruption, body: <>A droplet disruption ends the test before a normal flame extinction.<Cite p={19} /> NASA attributes methanol disruptions probably to fuel contamination (see the caveats below).<Cite p={17} /></> },
  ];

  return (
    <div className="space-y-12 lg:space-y-16">
      <PageHeader
        eyebrow="Microgravity Science"
        title="Fire Without Gravity"
        subtitle="What NASA's Flame Extinguishment Experiment did on the International Space Station, and why it matters for spacecraft fire safety. Every statement links to the page of the NASA report it comes from."
      />

      <GlassCard glow className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <div className="flex items-start gap-3">
          <BookOpen className="mt-0.5 size-5 shrink-0 text-prov-observed" aria-hidden="true" />
          <p className="text-sm text-ink-2">
            Source for this page: <span className="text-ink">{REPORT.short}</span>, <em>Detailed Results From the Flame Extinguishment Experiment (FLEX), March 2009 to December 2011</em> (Dietrich et al., NASA Glenn, 2015). Chips like <Cite p={2} className="ml-0" /> open the NASA PDF at that page.
          </p>
        </div>
        <ProvenanceBadge kind="observed" className="self-start sm:self-center" />
      </GlassCard>

      <Section id="gravity" eyebrow="1 · The physics" title="Why burn droplets in space?" icon={Orbit}>
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-center">
          <div className="space-y-4">
            <P>A single fuel droplet burning in still air is a classic problem in combustion research, first studied in the early 1950s.<Cite p={2} /></P>
            <P>If the flame stays spherical, only one spatial dimension matters. That makes the process far easier to model and to compare with theory.<Cite p={2} /></P>
            <P>On Earth, natural convection destroys that spherical symmetry. Researchers realised in 1956 that microgravity experiments could restore it, and NASA has used this for many years.<Cite p={2} /></P>
            <P>On the ISS the residual gravity was low enough that buoyant flow could be treated as negligible. Small vibrations (“g-jitter”) still made droplets drift, sometimes out of the cameras’ view.<Cite p={5} /><Cite p={16} /></P>
          </div>
          <GravityFlame />
        </div>
      </Section>

      <Section id="safety" eyebrow="2 · The question" title="When does a fire go out by itself?" icon={ShieldAlert}>
        <div className="grid gap-4 md:grid-cols-3">
          {[
            <>A principal objective was the <span className="text-ink">limiting oxygen index</span>: the oxygen percentage below which combustion does not occur. It reflects FLEX’s focus on spacecraft fire safety.<Cite p={2} /></>,
            <>Each series started at its highest oxygen level. The atmosphere was then diluted step by step, with nitrogen or CO₂, until quasi-steady burning was no longer observed.<Cite p={11} /><Cite p={13} /></>,
            <>The CO₂ series started from 1 atm at 21% O₂ and from 0.7 atm at 30% O₂. These match the ISS’s normal atmosphere, its spacewalk pre-breathe atmosphere and the highest oxygen level proposed for future exploration vehicles.<Cite p={13} /></>,
          ].map((body, i) => (
            <GlassCard key={i} className="p-5"><p className="text-sm leading-relaxed text-ink-2">{body}</p></GlassCard>
          ))}
        </div>
        <P>NASA reports that the observed limiting oxygen values for these fuels appear slightly lower than initially expected.<Cite p={2} /> The report deliberately does not interpret the results further: its purpose is to archive the data for future analysis.<Cite p={2} /><Cite p={17} /></P>
      </Section>

      <Section id="apparatus" eyebrow="3 · The hardware" title="Inside the combustion chamber" icon={Microscope}>
        <ApparatusDiagram />
      </Section>

      <Section id="sequence" eyebrow="4 · One test" title="One test, step by step" icon={Timer}>
        <TestSequence />
      </Section>

      <Section id="outcomes" eyebrow="5 · The result" title="Three ways a test ends" icon={Gauge}>
        <div className="grid gap-4 md:grid-cols-3">
          {outcomes.map((o, i) => (
            <motion.div key={o.key} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }}>
              <GlassCard className="h-full space-y-3 p-5">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2 font-display text-base font-semibold text-ink"><OutcomeShape outcome={o.key} className="size-3" />{OUTCOME_LABEL[o.key]}</span>
                  <span className="font-mono text-2xl font-bold tabular-nums text-ink">{o.n ?? "—"}</span>
                </div>
                <p className="text-sm leading-relaxed text-ink-2">{o.body}</p>
              </GlassCard>
            </motion.div>
          ))}
        </div>
        <p className="flex flex-wrap items-center gap-2 text-xs text-ink-3">
          <ProvenanceBadge kind="observed" compact /> Counts: the {e?.total ?? "—"} tests in the NASA PSI-69 dataset (2009–2011). FlameGuard counts completion and disruption as &quot;kept burning&quot;.
        </p>
      </Section>

      <Section id="measurement" eyebrow="6 · The measurements" title="How precise is the data?" icon={Ruler}>
        <div className="grid gap-6 lg:grid-cols-2 lg:items-center">
          <Uncertainty />
          <div className="space-y-3">
            <P>The flames are very dim, which makes the flame edge much harder to measure than the droplet.<Cite p={8} /> Measuring projected area instead of a single width reduced the uncertainty.<Cite p={8} /><Cite p={9} /></P>
            <P>Colour-camera flame diameters are typically about three-quarters of the UV-camera ones. The UV camera sees OH emission, which peaks outside the visible flame.<Cite p={16} /></P>
          </div>
        </div>
      </Section>

      <Section id="caveats" eyebrow="7 · Read with care" title="Caveats NASA reports" icon={CircleAlert}>
        <div className="grid gap-4 md:grid-cols-2">
          <GlassCard className="space-y-2 border-risk-elevated/30 p-5 md:col-span-2">
            <h3 className="font-display text-base font-semibold text-ink">Contaminated fuel needles</h3>
            <p className="text-sm leading-relaxed text-ink-2">
              A conformal coating on the fuel-dispensing needles could dissolve and flake into the fuel, so droplets in these tests held an unknown amount of it.<Cite p={16} />
              NASA judges burning rates, flame sizes and radiative extinction diameters minimally affected or unaffected. However, it states that disruptive extinction of methanol is <span className="text-ink">probably due to the contaminant</span>, and that no conclusion can be drawn for heptane.<Cite p={17} />
            </p>
            <p className="rounded-lg border border-risk-elevated/25 bg-risk-elevated/[0.06] p-3 text-xs leading-relaxed text-ink-2">
              <span className="font-semibold text-ink">What this means for FlameGuard:</span> the model counts disruption as &quot;kept burning&quot;. Some of those outcomes may reflect contamination rather than the atmosphere. This is recorded as a known limitation in the{" "}
              <a className="text-plasma hover:underline" href="https://github.com/souwmo04/FlameGuard-AI-NASA-fire-safety-dashboard/blob/main/docs/model_card.md#known-limitations" target="_blank" rel="noreferrer">model card</a>.
            </p>
          </GlassCard>
          <GlassCard className="space-y-2 p-5">
            <h3 className="font-display text-base font-semibold text-ink">Smudged UV window</h3>
            <p className="text-sm leading-relaxed text-ink-2">The UV camera&apos;s viewing window became dirty early in testing. That made flame images asymmetric and added uncertainty to flame measurements.<Cite p={7} /></p>
          </GlassCard>
          <GlassCard className="space-y-2 p-5">
            <h3 className="font-display text-base font-semibold text-ink">Drifting droplets</h3>
            <p className="text-sm leading-relaxed text-ink-2">Free droplets were rarely motionless. Some drifted out of a camera&apos;s view, so some data end early or have gaps.<Cite p={16} /></p>
          </GlassCard>
        </div>
      </Section>

      <Section id="flameguard" eyebrow="8 · From experiment to insight" title="How FlameGuard uses this data" icon={ArrowRight}>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { href: "/experiments", title: "Explore every test", body: "All tests with their NASA measurements and notes." },
            { href: "/risk", title: "Estimate Fire Risk", body: "A model trained on these outcomes, with its evidence." },
            { href: "/suppressants", title: "Compare suppressants", body: "What the observed tests can — and cannot — show." },
            { href: "/knowledge", title: "Ask the report", body: "Questions answered from this report, with citations." },
          ].map((c) => (
            <Link key={c.href} href={c.href} className="group">
              <GlassCard className="h-full space-y-1.5 p-4 transition group-hover:border-flame/30">
                <p className="flex items-center justify-between font-display text-sm font-semibold text-ink">{c.title}<ArrowRight className="size-4 text-ink-3 transition group-hover:translate-x-0.5 group-hover:text-flame" aria-hidden="true" /></p>
                <p className="text-xs text-ink-3">{c.body}</p>
              </GlassCard>
            </Link>
          ))}
        </div>
      </Section>

      <footer className="space-y-2 border-t border-white/[0.06] pt-6 text-xs leading-relaxed text-ink-3">
        <p className="label-caps text-[0.625rem]">Reference</p>
        <p>
          {REPORT.title}{" "}
          <a href={REPORT.record} target="_blank" rel="noreferrer" className="text-plasma hover:underline">NTRS 20150023456</a>. Public use permitted.
        </p>
        <p>Data: NASA Physical Sciences Informatics, FLEX (PSI-69), CC0-1.0, doi:10.60555/mbq8-0451. Illustrations on this page are schematic and not to scale.</p>
      </footer>
    </div>
  );
}
