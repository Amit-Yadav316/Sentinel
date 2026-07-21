import { LineChart, Line, ResponsiveContainer, YAxis, Tooltip } from "recharts";
import { useStore } from "../store/store";
import { CorridorMap } from "../components/CorridorMap";
import { EvidencePanel } from "../components/EvidencePanel";
import { SignalFeed } from "../components/SignalFeed";
import { riskLabel, riskTextColor } from "../lib/format";

export function MapScreen() {
  const { corridors, risk, vessels, vesselSource, news, newsSource, selectedCorridor, selectCorridor, brentSeries, lastEventHeadline } =
    useStore();
  const selectedRisk = risk.find((r) => r.corridor === selectedCorridor) ?? null;

  return (
    <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-3">
      <div className="flex flex-col gap-4 lg:col-span-2">
        <div className="card relative flex-1 overflow-hidden">
          <div className="absolute left-3 top-3 z-10 flex items-center gap-2">
            <span className="chip border border-line bg-surface/90 text-slate-600">Live corridor risk map</span>
            {vesselSource === "live" ? (
              <span className="chip border border-emerald-200 bg-emerald-50 text-emerald-700">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 live-dot" /> live AIS · {vessels.length} vessels
              </span>
            ) : (
              <span className="chip border border-fuchsia-200 bg-fuchsia-50 text-fuchsia-700">
                vessels simulated
              </span>
            )}
          </div>
          {lastEventHeadline && (
            <div className="absolute bottom-3 left-3 right-3 z-10 rounded-lg border border-line bg-surface/95 px-3 py-2 text-[12px] text-slate-700 shadow-sm">
              <span className="mr-2 font-mono text-[10px] uppercase tracking-wider text-accent">latest signal</span>
              {lastEventHeadline}
            </div>
          )}
          <CorridorMap
            corridors={corridors}
            risk={risk}
            vessels={vessels}
            selected={selectedCorridor}
            onSelect={selectCorridor}
          />
        </div>

        <div className="grid grid-cols-5 gap-2">
          {[...risk]
            .sort((a, b) => b.score - a.score)
            .map((r) => (
              <button
                key={r.corridor}
                onClick={() => selectCorridor(r.corridor)}
                className={`card p-2.5 text-left transition ${
                  selectedCorridor === r.corridor ? "ring-2 ring-accent" : "hover:border-slate-300"
                }`}
              >
                <div className="truncate text-[11px] text-slate-500">{r.name}</div>
                <div className="num text-xl font-bold" style={{ color: riskTextColor(r.score) }}>
                  {r.score.toFixed(0)}
                </div>
                <div className="text-[9px] font-semibold" style={{ color: riskTextColor(r.score) }}>
                  {riskLabel(r.score)}
                </div>
              </button>
            ))}
        </div>
      </div>

      <div className="flex min-h-0 flex-col gap-4">
        <div className="min-h-0 flex-1">
          <EvidencePanel risk={selectedRisk} />
        </div>
        <div className="card shrink-0 p-3">
          <div className="mb-1 flex items-center justify-between">
            <span className="stat-label">Brent (30d)</span>
            <span className="num text-sm text-slate-700">
              ${brentSeries.at(-1)?.value.toFixed(1) ?? "—"}
            </span>
          </div>
          <div className="h-16">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={brentSeries}>
                <YAxis hide domain={["dataMin - 2", "dataMax + 2"]} />
                <Tooltip
                  contentStyle={{ background: "#ffffff", border: "1px solid #e4e3dd", fontSize: 11, borderRadius: 8 }}
                  labelStyle={{ color: "#64748b" }}
                />
                <Line type="monotone" dataKey="value" stroke="#2a78d6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="shrink-0">
          <SignalFeed items={news} source={newsSource} />
        </div>
      </div>
    </div>
  );
}
