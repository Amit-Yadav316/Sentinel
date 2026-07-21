import { useStore } from "../store/store";
import { riskTextColor } from "../lib/format";

export function StatusBar() {
  const { brent, risk, demoRunning, demoStep, demoTotal, startEscalation, wsConnected } = useStore();
  const maxRisk = risk.reduce((m, r) => Math.max(m, r.score), 0);
  const sprDays = 9.5; // strategic cover, from assumptions.yaml

  return (
    <header className="flex items-center justify-between border-b border-line bg-surface px-5 py-2.5">
      <div className="flex items-center gap-2.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-white">
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
            <path d="M12 2 4 6v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6l-8-4Z" />
          </svg>
        </div>
        <div>
          <div className="text-sm font-semibold leading-none text-slate-900">SENTINEL</div>
          <div className="text-[10px] leading-none text-slate-500">Energy Supply Chain Resilience</div>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <Stat label="Brent" value={`$${brent.toFixed(1)}`} sub="/bbl" />
        <Stat label="Strategic SPR" value={sprDays.toFixed(1)} sub="days" />
        <div className="text-center">
          <div className="stat-label">Max corridor risk</div>
          <div className="num text-lg font-bold leading-tight" style={{ color: riskTextColor(maxRisk) }}>
            {maxRisk.toFixed(0)}
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className={`h-2 w-2 rounded-full ${wsConnected ? "bg-emerald-500 live-dot" : "bg-slate-300"}`} />
          {wsConnected ? "live" : "offline"}
        </div>
        <button
          onClick={startEscalation}
          disabled={demoRunning}
          className="rounded-lg bg-accent px-3.5 py-1.5 text-sm font-semibold text-white shadow-sm transition hover:bg-accent-600 disabled:opacity-50"
        >
          {demoRunning ? `Injecting ${demoStep}/${demoTotal}…` : "▶ Run escalation demo"}
        </button>
      </div>
    </header>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="text-center">
      <div className="stat-label">{label}</div>
      <div className="num text-lg font-bold leading-tight text-slate-900">
        {value}
        <span className="ml-0.5 text-[11px] font-normal text-slate-400">{sub}</span>
      </div>
    </div>
  );
}
