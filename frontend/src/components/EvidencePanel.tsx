import type { CorridorRisk } from "../lib/types";
import { riskColor, riskLabel, riskTextColor } from "../lib/format";
import { Chip } from "./Chip";

export function EvidencePanel({ risk }: { risk: CorridorRisk | null }) {
  if (!risk) {
    return (
      <div className="card flex items-center justify-center p-8 text-center text-base text-slate-500">
        Select a corridor to view its risk evidence trail.
      </div>
    );
  }
  const fill = riskColor(risk.score);
  const textColor = riskTextColor(risk.score);
  return (
    <div className="card overflow-hidden">
      <div className="border-b border-line p-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-sm text-slate-500">Corridor risk</div>
            <div className="mt-0.5 text-lg font-semibold text-slate-900">{risk.name}</div>
          </div>
          <div className="text-right">
            <div className="num text-5xl font-bold" style={{ color: textColor }}>
              {risk.score.toFixed(0)}
            </div>
            <div className="text-sm font-semibold" style={{ color: textColor }}>
              {riskLabel(risk.score)}
            </div>
          </div>
        </div>
        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full transition-all duration-700"
            style={{ width: `${risk.score}%`, background: fill }} />
        </div>
      </div>

      <div className="px-5 pb-2 pt-3 text-sm font-medium text-slate-600">
        Evidence trail{risk.contributions.length > 0 ? ` · ${risk.contributions.length} signals` : ""}
      </div>

      <div className="max-h-[280px] space-y-2.5 overflow-y-auto px-5 pb-5">
        {risk.contributions.length === 0 && (
          <div className="text-base text-slate-500">No active events — resting at structural baseline.</div>
        )}
        {risk.contributions.map((c, i) => (
          <div key={i} className="rounded-lg border border-line bg-slate-50/70 p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="text-[15px] leading-snug text-slate-700">{c.headline}</div>
              <div className="num shrink-0 text-base font-semibold text-accent">
                +{c.contribution.toFixed(1)}
              </div>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Chip tone="info">{c.event_type.replace(/_/g, " ")}</Chip>
              <span className="text-xs text-slate-400">
                {c.age_hours < 1 ? "just now" : `${Math.round(c.age_hours)}h ago`}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
