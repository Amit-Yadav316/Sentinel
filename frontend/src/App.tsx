import { useEffect, useState } from "react";
import { useStore } from "./store/store";
import { StatusBar } from "./components/StatusBar";
import { MapScreen } from "./screens/MapScreen";
import { ScenarioScreen } from "./screens/ScenarioScreen";
import { RecommendationsScreen } from "./screens/RecommendationsScreen";
import { BacktestScreen } from "./screens/BacktestScreen";

type Screen = "map" | "scenario" | "recs" | "backtest";

const NAV: { id: Screen; label: string; icon: string }[] = [
  { id: "map", label: "Corridor Risk Map", icon: "M12 2C8 2 5 5 5 9c0 5 7 13 7 13s7-8 7-13c0-4-3-7-7-7Zm0 9a2 2 0 1 1 0-4 2 2 0 0 1 0 4Z" },
  { id: "scenario", label: "Scenario Console", icon: "M4 4h16v4H4V4Zm0 6h16v10H4V10Zm3 3v4m4-4v4m4-4v4" },
  { id: "recs", label: "Procurement", icon: "M9 11l3 3 8-8M4 12a8 8 0 1 0 16 0 8 8 0 0 0-16 0Z" },
  { id: "backtest", label: "Historical Backtest", icon: "M3 3v18h18M7 15l3-4 3 3 5-7" },
];

export default function App() {
  const [screen, setScreen] = useState<Screen>("map");
  const { loadAll, connect, activeRunId, recommendations } = useStore();

  useEffect(() => {
    loadAll().catch(console.error);
    connect();
  }, [loadAll, connect]);

  // When the demo auto-runs a scenario, we DON'T yank the screen away — you
  // stay in control and click across yourself. The nav items just pulse to
  // show fresh results are waiting.
  function badgeFor(id: Screen): boolean {
    if (id === "scenario") return activeRunId !== null;
    if (id === "recs") return recommendations.length > 0;
    return false;
  }

  return (
    <div className="flex h-full flex-col">
      <StatusBar />
      <div className="flex min-h-0 flex-1">
        <nav className="flex w-48 shrink-0 flex-col gap-1 border-r border-line bg-surface p-3">
          {NAV.map((n) => {
            const active = screen === n.id;
            return (
              <button
                key={n.id}
                onClick={() => setScreen(n.id)}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition ${
                  active ? "bg-accent-soft text-accent-600" : "text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                }`}
              >
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={1.8}>
                  <path d={n.icon} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span className="flex-1">{n.label}</span>
                {!active && badgeFor(n.id) && <span className="h-1.5 w-1.5 rounded-full bg-accent live-dot" />}
              </button>
            );
          })}
          <div className="mt-auto rounded-lg border border-line bg-slate-50 p-3 text-xs leading-relaxed text-slate-500">
            <div className="mb-1 font-semibold text-slate-700">Response loop</div>
            Signal → risk → scenario → executable recommendation, in under 5 minutes.
          </div>
        </nav>

        <main className="min-h-0 flex-1 overflow-auto p-4">
          {screen === "map" && <MapScreen />}
          {screen === "scenario" && <ScenarioScreen />}
          {screen === "recs" && <RecommendationsScreen />}
          {screen === "backtest" && <BacktestScreen />}
        </main>
      </div>
    </div>
  );
}
