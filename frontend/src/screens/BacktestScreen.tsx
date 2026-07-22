import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useStore } from "../store/store";
import { riskColor } from "../lib/format";

function fmtDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function BacktestScreen() {
  const { backtest: bt } = useStore();

  if (!bt) {
    return (
      <div className="card mx-auto max-w-3xl p-8 text-center text-base text-slate-500">
        Loading the June 2025 backtest…
      </div>
    );
  }

  const brentByDate = new Map(bt.brent_series.map((b) => [b.date, b.value]));
  const data = bt.risk_series.map((r) => ({
    date: r.date,
    label: fmtDate(r.date),
    risk: r.score,
    brent: brentByDate.get(r.date) ?? null,
  }));
  const crossLabel = bt.risk_cross_date ? fmtDate(bt.risk_cross_date) : undefined;
  const peakLabel = fmtDate(bt.brent_peak.date);

  return (
    <div className="mx-auto max-w-[1200px] space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Historical Backtest — June 2025 Escalation</h1>
        <p className="mt-0.5 text-base text-slate-500">
          The <b className="text-slate-700">same risk model</b>, replayed on the June 2025 Israel–Iran /
          Strait-of-Hormuz escalation. Real dated headlines in; Brent overlaid.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div className="card p-4">
          <div className="stat-label">First CRITICAL</div>
          <div className="mt-1 text-2xl font-bold text-red-600">{crossLabel ?? "—"}</div>
          <div className="mt-0.5 text-xs text-slate-500">risk crossed 70 as strikes began</div>
        </div>
        <div className="card p-4">
          <div className="stat-label">Brent single-session</div>
          <div className="mt-1 text-2xl font-bold text-amber-600">+{bt.brent_spike.pct.toFixed(1)}%</div>
          <div className="mt-0.5 text-xs text-slate-500">on {fmtDate(bt.brent_spike.date)}</div>
        </div>
        <div className="card p-4">
          <div className="stat-label">Critical warning window</div>
          <div className="mt-1 text-2xl font-bold text-accent">{bt.lead_days ?? "—"} days</div>
          <div className="mt-0.5 text-xs text-slate-500">from first alert to Brent's peak</div>
        </div>
        <div className="card p-4">
          <div className="stat-label">Peak risk</div>
          <div className="mt-1 text-2xl font-bold" style={{ color: riskColor(bt.peak_risk.score) }}>
            {bt.peak_risk.score.toFixed(0)}
          </div>
          <div className="mt-0.5 text-xs text-slate-500">on {fmtDate(bt.peak_risk.date)}</div>
        </div>
      </div>

      {/* risk chart */}
      <div className="card p-4">
        <div className="mb-1 text-sm font-semibold text-slate-800">Hormuz corridor risk (our model)</div>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 6, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="#eef1f4" vertical={false} />
              <XAxis dataKey="label" tick={false} axisLine={{ stroke: "#e4e3dd" }} height={4} />
              <YAxis width={40} domain={[40, 100]} tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "#fff", border: "1px solid #e4e3dd", borderRadius: 8, fontSize: 12 }} />
              <ReferenceLine y={bt.threshold} stroke="#d03b3b" strokeDasharray="5 4"
                label={{ value: "alert 70", position: "right", fill: "#d03b3b", fontSize: 11 }} />
              {crossLabel && <ReferenceLine x={crossLabel} stroke="#d03b3b" strokeDasharray="3 3" />}
              <Line type="monotone" dataKey="risk" stroke="#1c5cab" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* brent chart, aligned x-axis */}
      <div className="card p-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-sm font-semibold text-slate-800">Brent crude ($/bbl)</span>
          <span className="text-xs text-slate-400">{bt.brent_note}</span>
        </div>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 6, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="#eef1f4" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#94a3b8" }} interval={2}
                axisLine={{ stroke: "#e4e3dd" }} tickLine={false} />
              <YAxis width={40} domain={["dataMin - 2", "dataMax + 2"]} tick={{ fontSize: 11, fill: "#94a3b8" }}
                axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "#fff", border: "1px solid #e4e3dd", borderRadius: 8, fontSize: 12 }} />
              {crossLabel && <ReferenceLine x={crossLabel} stroke="#d03b3b" strokeDasharray="3 3"
                label={{ value: "risk alert", position: "top", fill: "#d03b3b", fontSize: 10 }} />}
              <ReferenceLine x={peakLabel} stroke="#eab308" strokeDasharray="3 3"
                label={{ value: "Brent peak", position: "top", fill: "#a06b00", fontSize: 10 }} />
              <Line type="monotone" dataKey="brent" stroke="#334e68" strokeWidth={2.5} dot={false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <div className="mb-2 text-sm font-semibold text-slate-800">What the model saw</div>
          <div className="max-h-64 space-y-2 overflow-y-auto">
            {bt.headlines.map((h, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <span className="mt-1 w-14 shrink-0 text-xs font-medium text-slate-500">{fmtDate(h.date)}</span>
                <span
                  className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
                  style={{ background: riskColor(h.severity * 100 + 20) }}
                />
                <span className="text-sm leading-snug text-slate-700">{h.headline}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card flex flex-col justify-center gap-3 p-5">
          <div className="text-sm font-semibold text-slate-800">The takeaway</div>
          <p className="text-[15px] leading-relaxed text-slate-600">
            The score climbed from its <b className="text-slate-800">45 baseline</b> as tensions built (Jun 9–12),
            hit <b className="text-red-600">CRITICAL on Jun 13</b> as the strikes began, and stayed critical
            through Brent's run-up to its <b className="text-slate-800">Jun 20 peak</b> — then flagged the{" "}
            <b className="text-slate-800">Jun 23</b> US-strike escalation too.
          </p>
          <p className="text-[15px] leading-relaxed text-slate-600">
            Every threshold breach <b className="text-slate-800">auto-fires reroute recommendations in minutes</b> —
            against a historical <b className="text-slate-800">47-day</b> manual stabilization gap.
          </p>
        </div>
      </div>
    </div>
  );
}
