export const fmtKbd = (v: number) => `${v.toLocaleString(undefined, { maximumFractionDigits: 0 })} kb/d`;
export const fmtUsd = (v: number) => `${v >= 0 ? "+" : "−"}$${Math.abs(v).toFixed(1)}/bbl`;
export const fmtInr = (v: number) => `₹${v.toFixed(2)}/L`;
export const fmtDays = (v: number) => (v < 0 ? "∞" : `${v.toFixed(0)} days`);
export const fmtPct = (v: number) => `${v.toFixed(1)}%`;

// Status ramp (validated reference palette). Vivid values are for FILLS —
// bars, arcs, dots, meters. On a light surface warning/serious fall below 3:1,
// so numbers use the darker `riskTextColor` and every score keeps its label.
export function riskColor(score: number): string {
  if (score >= 70) return "#d03b3b"; // critical
  if (score >= 55) return "#ec835a"; // serious
  if (score >= 40) return "#fab219"; // warning
  return "#0ca30c"; // good
}

// Contrast-safe (~4.5:1 on white) variants for colored numbers/text.
export function riskTextColor(score: number): string {
  if (score >= 70) return "#b42323";
  if (score >= 55) return "#b0491f";
  if (score >= 40) return "#8a6100";
  return "#0a7d0a";
}

export function riskLabel(score: number): string {
  if (score >= 70) return "CRITICAL";
  if (score >= 55) return "ELEVATED";
  if (score >= 40) return "WATCH";
  return "NORMAL";
}
