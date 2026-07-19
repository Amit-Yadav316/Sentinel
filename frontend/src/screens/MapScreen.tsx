import { LineChart, Line, ResponsiveContainer, YAxis, Tooltip } from "recharts";
import { useStore } from "../store/store";
import { CorridorMap } from "../components/CorridorMap";
import { EvidencePanel } from "../components/EvidencePanel";
import { riskColor, riskLabel } from "../lib/format";

export function MapScreen() {
  const { corridors, risk, vessels, selectedCorridor, selectCorridor, brentSeries, lastEventHeadline } =
    useStore();
  const selectedRisk = risk.find((r) => r.corridor === selectedCorridor) ?? null;

  return (
    <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-3">
      <div className="flex flex-col gap-4 lg:col-span-2">
        <div className="card relative flex-1 overflow-hidden">
          <div className="absolute left-3 top-3 z-10 flex items-center gap-2">
            <span className="chip bg-ink-900/80 text-slate-300">Live corridor risk map</span>
            <span className="chip bg-fuchsia-500/15 text-fuchsia-300 border border-fuchsia-500/30">
              vessels simulated
            </span>
          </div>
          {lastEventHeadline && (
            <div className="absolute bottom-3 left-3 right-3 z-10 rounded-lg border border-ink-500 bg-ink-900/85 px-3 py-2 text-[12px] text-slate-300">
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
                  selectedCorridor === r.corridor ? "ring-1 ring-accent" : "hover:border-ink-500"
                }`}
              >
                <div className="truncate text-[11px] text-slate-400">{r.name}</div>
                <div className="num text-xl font-bold" style={{ color: riskColor(r.score) }}>
                  {r.score.toFixed(0)}
                </div>
                <div className="text-[9px] font-semibold" style={{ color: riskColor(r.score) }}>
                  {riskLabel(r.score)}
                </div>
              </button>
            ))}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <EvidencePanel risk={selectedRisk} />
        <div className="card p-3">
          <div className="mb-1 flex items-center justify-between">
            <span className="stat-label">Brent (30d)</span>
            <span className="num text-sm text-slate-300">
              ${brentSeries.at(-1)?.value.toFixed(1) ?? "—"}
            </span>
          </div>
          <div className="h-16">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={brentSeries}>
                <YAxis hide domain={["dataMin - 2", "dataMax + 2"]} />
                <Tooltip
                  contentStyle={{ background: "#0a0e17", border: "1px solid #2a3352", fontSize: 11 }}
                  labelStyle={{ color: "#94a3b8" }}
                />
                <Line type="monotone" dataKey="value" stroke="#38bdf8" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
