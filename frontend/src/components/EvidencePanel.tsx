import type { CorridorRisk } from "../lib/types";
import { riskColor, riskLabel, riskTextColor } from "../lib/format";
import { Chip } from "./Chip";

export function EvidencePanel({ risk }: { risk: CorridorRisk | null }) {
  if (!risk) {
    return (
      <div className="card flex h-full items-center justify-center p-6 text-center text-sm text-slate-500">
        Select a corridor on the map to see the evidence behind its risk score.
      </div>
    );
  }
  const fill = riskColor(risk.score);
  const textColor = riskTextColor(risk.score);
  return (
    <div className="card flex h-full flex-col overflow-hidden">
      <div className="border-b border-line p-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="stat-label">Corridor risk</div>
            <div className="mt-0.5 text-lg font-semibold text-slate-900">{risk.name}</div>
          </div>
          <div className="text-right">
            <div className="num text-4xl font-bold" style={{ color: textColor }}>
              {risk.score.toFixed(0)}
            </div>
            <div className="text-[11px] font-semibold" style={{ color: textColor }}>
              {riskLabel(risk.score)}
            </div>
          </div>
        </div>
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full transition-all duration-700"
            style={{ width: `${risk.score}%`, background: fill }} />
        </div>
        <div className="mt-2 font-mono text-[11px] text-slate-500">{risk.formula}</div>
      </div>

      <div className="flex items-center justify-between px-4 py-2 text-[11px] text-slate-500">
        <span>Evidence trail — {risk.contributions.length} signals</span>
        <span>baseline {risk.baseline} · Σ {risk.weighted_sum.toFixed(2)}</span>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto px-4 pb-4">
        {risk.contributions.length === 0 && (
          <div className="text-sm text-slate-500">No events yet — resting at structural baseline.</div>
        )}
        {risk.contributions.map((c, i) => (
          <div key={i} className="rounded-lg border border-line bg-slate-50/60 p-2.5">
            <div className="flex items-start justify-between gap-2">
              <div className="text-[13px] leading-snug text-slate-700">{c.headline}</div>
              <div className="num shrink-0 text-sm font-semibold text-accent">
                +{c.contribution.toFixed(2)}
              </div>
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              <Chip tone="info">{c.event_type.replace(/_/g, " ")}</Chip>
              <span className="num text-[10px] text-slate-400">
                sev {c.severity} × w {c.weight} × decay {c.decay} · {c.age_hours}h old
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
