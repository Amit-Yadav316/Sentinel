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
    <div className="mx-auto max-w-[1500px] space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Import Corridor Risk</h1>
        <p className="mt-0.5 text-base text-slate-500">
          Live disruption risk across the maritime corridors supplying India's crude. Select a corridor
          to view its evidence trail.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* left: map + corridor tiles */}
        <div className="space-y-5 lg:col-span-2">
          <div className="card relative h-[460px] overflow-hidden">
            <div className="absolute left-4 top-4 z-10 flex items-center gap-2">
              <span className="chip border border-line bg-surface/90 text-slate-600">Live corridor risk</span>
              {vesselSource === "live" ? (
                <span className="chip border border-emerald-200 bg-emerald-50 text-emerald-700">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 live-dot" /> Live AIS · {vessels.length} vessels
                </span>
              ) : (
                <span className="chip border border-fuchsia-200 bg-fuchsia-50 text-fuchsia-700">
                  Vessels: simulated
                </span>
              )}
            </div>
            {lastEventHeadline && (
              <div className="absolute bottom-4 left-4 right-4 z-10 rounded-lg border border-line bg-surface/95 px-4 py-2.5 text-sm text-slate-700 shadow-sm">
                <span className="mr-2 font-semibold text-accent">Latest signal</span>
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

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {[...risk]
              .sort((a, b) => b.score - a.score)
              .map((r) => (
                <button
                  key={r.corridor}
                  onClick={() => selectCorridor(r.corridor)}
                  className={`card p-4 text-left transition ${
                    selectedCorridor === r.corridor ? "ring-2 ring-accent" : "hover:border-slate-300"
                  }`}
                >
                  <div className="truncate text-sm text-slate-500">{r.name}</div>
                  <div className="mt-1 text-4xl font-bold" style={{ color: riskTextColor(r.score) }}>
                    {r.score.toFixed(0)}
                  </div>
                  <div className="text-xs font-semibold" style={{ color: riskTextColor(r.score) }}>
                    {riskLabel(r.score)}
                  </div>
                </button>
              ))}
          </div>
        </div>

        {/* right: details */}
        <div className="space-y-5">
          <EvidencePanel risk={selectedRisk} />

          <div className="card p-4">
            <div className="mb-1.5 flex items-center justify-between">
              <span className="stat-label">Brent crude — last 30 days</span>
              <span className="num text-base font-semibold text-slate-800">
                ${brentSeries.at(-1)?.value.toFixed(1) ?? "—"}
              </span>
            </div>
            <div className="h-20">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={brentSeries}>
                  <YAxis hide domain={["dataMin - 2", "dataMax + 2"]} />
                  <Tooltip
                    contentStyle={{ background: "#ffffff", border: "1px solid #e4e3dd", fontSize: 12, borderRadius: 8 }}
                    labelStyle={{ color: "#64748b" }}
                  />
                  <Line type="monotone" dataKey="value" stroke="#2a78d6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <SignalFeed items={news} source={newsSource} />
        </div>
      </div>
    </div>
  );
}
