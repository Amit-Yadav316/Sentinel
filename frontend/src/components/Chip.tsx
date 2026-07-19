import type { ReactNode } from "react";

type Tone = "sim" | "warn" | "danger" | "info" | "ok";

const TONES: Record<Tone, string> = {
  sim: "bg-fuchsia-500/15 text-fuchsia-300 border border-fuchsia-500/30",
  warn: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
  danger: "bg-red-500/15 text-red-300 border border-red-500/30",
  info: "bg-sky-500/15 text-sky-300 border border-sky-500/30",
  ok: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
};

export function Chip({ tone = "info", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`chip ${TONES[tone]}`}>{children}</span>;
}

export function SimChip() {
  return (
    <Chip tone="sim">
      <span className="h-1.5 w-1.5 rounded-full bg-fuchsia-400" /> simulated
    </Chip>
  );
}
