import type { ScenarioResult as Result } from "../lib/types";
import { fmtDays, fmtInr, fmtKbd, fmtPct, fmtUsd } from "../lib/format";
import { Formula } from "./Formula";

export function ScenarioResultView({ result }: { result: Result }) {
  const maxShort = Math.max(1, ...result.refinery_shortfalls.map((s) => s.shortfall_kbd));
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi
          label="Supply gap"
          value={fmtKbd(result.supply_gap_kbd)}
          sub={fmtPct(result.supply_gap_pct) + " of net imports"}
          formula={result.formulas.supply_gap_kbd}
          tone="danger"
        />
        <Kpi
          label="SPR runway vs gap"
          value={fmtDays(result.spr_runway_days)}
          sub={`reserve ${(result.reserve_kb / 1000).toFixed(0)} mmbbl`}
          formula={result.formulas.spr_runway_days}
          tone="warn"
        />
        <Kpi
          label="Landed cost Δ"
          value={fmtUsd(result.landed_cost_delta_usd_bbl)}
          sub={`Brent → $${result.brent_after_usd.toFixed(1)}`}
          formula={result.formulas.landed_cost_delta_usd_bbl}
          tone="warn"
        />
        <Kpi
          label="Retail pass-through"
          value={fmtInr(result.retail_passthrough_inr_l)}
          sub="est. pump impact"
          formula={result.formulas.retail_passthrough_inr_l}
          tone="danger"
        />
      </div>

      <div>
        <div className="mb-2 text-sm font-medium text-slate-500">Ripple into the wider economy</div>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Kpi
            label="Annual import bill"
            value={`+$${result.import_bill_delta_usd_bn.toFixed(0)}bn`}
            sub="added crude cost / yr"
            formula={result.formulas.import_bill_delta_usd_bn}
            tone="danger"
          />
          <Kpi
            label="GDP growth drag"
            value={`−${result.gdp_drag_pp.toFixed(2)} pp`}
            sub="est. hit to growth"
            formula={result.formulas.gdp_drag_pp}
            tone="warn"
          />
          <Kpi
            label="Current-account"
            value={`+${result.cad_widen_pp.toFixed(2)} pp`}
            sub="wider deficit (% GDP)"
            formula={result.formulas.cad_widen_pp}
            tone="warn"
          />
          <Kpi
            label="Power-sector stress"
            value={`${result.power_stress_index.toFixed(0)}/100`}
            sub="liquid-fuel exposure"
            formula={result.formulas.power_stress_index}
            tone="danger"
          />
        </div>
      </div>

      <div className="card p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-sm font-semibold text-slate-900">Refinery shortfall allocation</div>
          <Formula text={result.formulas.refinery_shortfall} />
        </div>
        <div className="space-y-2">
          {result.refinery_shortfalls.map((s) => (
            <div key={s.refinery_id} className="flex items-center gap-3">
              <div className="w-40 shrink-0 truncate text-[13px] text-slate-700">{s.name}</div>
              <div className="relative h-5 flex-1 overflow-hidden rounded bg-slate-100">
                <div
                  className="h-full rounded bg-gradient-to-r from-amber-400 to-red-500"
                  style={{ width: `${(s.shortfall_kbd / maxShort) * 100}%` }}
                />
              </div>
              <div className="num w-28 shrink-0 text-right text-[13px] text-slate-700">
                {s.shortfall_kbd.toFixed(0)} kb/d
                <span className="ml-1 text-slate-400">({s.shortfall_pct.toFixed(0)}%)</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Kpi({
  label,
  value,
  sub,
  formula,
  tone,
}: {
  label: string;
  value: string;
  sub: string;
  formula: string;
  tone: "danger" | "warn";
}) {
  const color = tone === "danger" ? "text-red-600" : "text-amber-600";
  return (
    <div className="card p-3.5">
      <div className="flex items-center justify-between">
        <span className="stat-label">{label}</span>
        <Formula text={formula} />
      </div>
      <div className={`num mt-1 text-2xl font-bold ${color}`}>{value}</div>
      <div className="mt-0.5 text-[11px] text-slate-500">{sub}</div>
    </div>
  );
}
