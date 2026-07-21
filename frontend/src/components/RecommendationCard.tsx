import type { Recommendation } from "../lib/types";
import { fmtUsd } from "../lib/format";
import { Chip, SimChip } from "./Chip";

export function RecommendationCard({ rec }: { rec: Recommendation }) {
  const p = rec.payload;
  const hasSanction = p.caveats.some((c) => c.toLowerCase().includes("sanction"));
  const cheaper = p.cost_delta_usd_bbl < 0;
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center gap-3 border-b border-line bg-slate-50 px-4 py-2.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent text-sm font-bold text-white">
          {rec.rank}
        </div>
        <div className="flex-1">
          <div className="text-[15px] font-semibold text-slate-900">{p.crude}</div>
          <div className="text-[11px] text-slate-500">
            {p.source} · via {p.route}
          </div>
        </div>
        <div className="text-right">
          <div className={`num text-lg font-bold ${cheaper ? "text-emerald-600" : "text-amber-600"}`}>
            {fmtUsd(p.cost_delta_usd_bbl)}
          </div>
          <div className="text-[10px] text-slate-400">cost delta</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-px bg-line text-center">
        <Metric label="Volume" value={`${p.volume_kbd.toFixed(0)}`} unit="kb/d" />
        <Metric label="ETA" value={`${p.eta_days}`} unit="days" />
        <Metric label="Availability" value={`${(p.availability_index * 100).toFixed(0)}`} unit="%" />
      </div>

      <div className="space-y-2.5 p-4">
        <p className="text-[13px] leading-relaxed text-slate-600">{p.rationale}</p>

        <div>
          <div className="stat-label mb-1">Compatible refineries · {p.compatible_count}</div>
          <div className="flex flex-wrap gap-1.5">
            {p.compatible_refineries.length ? (
              p.compatible_refineries.map((r) => (
                <Chip key={r} tone="ok">
                  {r}
                </Chip>
              ))
            ) : (
              <span className="text-[12px] text-slate-400">grade check pending / none in shortfall set</span>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5 pt-1">
          <Chip tone="neutral">load: {p.load_port}</Chip>
          {hasSanction && <Chip tone="danger">⚠ sanctions / price-cap flag</Chip>}
          <SimChip />
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="bg-surface py-2.5">
      <div className="num text-lg font-bold text-slate-900">{value}</div>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">
        {label} · {unit}
      </div>
    </div>
  );
}
