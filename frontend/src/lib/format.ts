export const fmtKbd = (v: number) => `${v.toLocaleString(undefined, { maximumFractionDigits: 0 })} kb/d`;
export const fmtUsd = (v: number) => `${v >= 0 ? "+" : "−"}$${Math.abs(v).toFixed(1)}/bbl`;
export const fmtInr = (v: number) => `₹${v.toFixed(2)}/L`;
export const fmtDays = (v: number) => (v < 0 ? "∞" : `${v.toFixed(0)} days`);
export const fmtPct = (v: number) => `${v.toFixed(1)}%`;

export function riskColor(score: number): string {
  if (score >= 70) return "#ef4444"; // crit
  if (score >= 55) return "#f97316"; // high
  if (score >= 40) return "#eab308"; // mid
  return "#22c55e"; // low
}

export function riskLabel(score: number): string {
  if (score >= 70) return "CRITICAL";
  if (score >= 55) return "ELEVATED";
  if (score >= 40) return "WATCH";
  return "NORMAL";
}
