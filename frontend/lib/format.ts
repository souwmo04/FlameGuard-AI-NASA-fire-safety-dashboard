/** Number formatting helpers. Values arrive from the API already computed; these only display them. */

export const formatInt = (n: number) => new Intl.NumberFormat("en-US").format(Math.round(n));

export const formatPercent = (fraction: number, digits = 0) => `${(fraction * 100).toFixed(digits)}%`;

export const formatDecimal = (n: number, digits = 3) => n.toFixed(digits);

/** Fire Risk without implying certainty at the extremes (mirrors the backend's format_risk). */
export function formatRisk(score: number): string {
  if (score > 99.5) return "> 99";
  if (score < 0.5) return "< 1";
  return Math.round(score).toString();
}
