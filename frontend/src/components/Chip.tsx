import type { ReactNode } from "react";

type Tone = "sim" | "warn" | "danger" | "info" | "ok" | "neutral";

const TONES: Record<Tone, string> = {
  sim: "bg-fuchsia-50 text-fuchsia-700 border border-fuchsia-200",
  warn: "bg-amber-50 text-amber-700 border border-amber-200",
  danger: "bg-red-50 text-red-700 border border-red-200",
  info: "bg-sky-50 text-sky-700 border border-sky-200",
  ok: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  neutral: "bg-slate-100 text-slate-600 border border-slate-200",
};

export function Chip({ tone = "info", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`chip ${TONES[tone]}`}>{children}</span>;
}

export function SimChip() {
  return (
    <Chip tone="sim">
      <span className="h-1.5 w-1.5 rounded-full bg-fuchsia-500" /> simulated
    </Chip>
  );
}
