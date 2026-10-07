import { cn } from "@/lib/cn";

export const REPORT = {
  short: "NASA/TP-2015-216046",
  title: "Dietrich, D. L., Ferkul, P. V., Bryg, V. M., Nayagam, M. V., Hicks, M. C., Williams, F. A., Dryer, F. L., Shaw, B. D., Choi, M. Y., Avedisian, C. T. (2015). Detailed Results From the Flame Extinguishment Experiment (FLEX), March 2009 to December 2011. NASA/TP-2015-216046, NASA Glenn Research Center.",
  record: "https://ntrs.nasa.gov/citations/20150023456",
  pdf: "https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf",
};

/** The report's printed page n is PDF page n + 6 (cover, report-documentation and contents pages come first). */
export const reportPage = (printed: number) => `${REPORT.pdf}#page=${printed + 6}`;

/** Citation chip for a statement taken from the NASA FLEX report; opens the PDF at that page. */
export function Cite({ p, to, className }: { p: number; to?: number; className?: string }) {
  const label = to ? `pp. ${p}–${to}` : `p. ${p}`;
  return (
    <a
      href={reportPage(p)}
      target="_blank"
      rel="noreferrer"
      title={`${REPORT.short}, ${label} (opens the NASA PDF)`}
      className={cn("ml-1 inline-flex items-center rounded-md border border-prov-observed/30 bg-prov-observed/10 px-1.5 py-px align-baseline font-mono text-[0.6875rem] font-semibold text-prov-observed no-underline transition hover:bg-prov-observed/20", className)}
    >
      <span className="sr-only">Source: {REPORT.short}, </span>{label}
    </a>
  );
}
