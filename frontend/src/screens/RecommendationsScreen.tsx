import { useStore } from "../store/store";
import { api } from "../lib/api";
import { RecommendationCard } from "../components/RecommendationCard";

export function RecommendationsScreen() {
  const { recommendations, runs, activeRunId } = useStore();
  const activeRun = runs.find((r) => r.id === activeRunId);

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <div className="card flex items-center justify-between p-4">
        <div>
          <div className="text-xs uppercase tracking-wider text-slate-400">
            Procurement rerouting recommendations
          </div>
          <div className="text-lg font-semibold text-slate-100">
            {activeRun ? activeRun.scenario_title : "No active scenario"}
          </div>
          {activeRun && (
            <div className="mt-0.5 text-[12px] text-slate-400">
              Replacing {activeRun.result.supply_gap_kbd.toFixed(0)} kb/d shortfall ·{" "}
              {activeRun.result.supply_gap_pct.toFixed(1)}% of net imports
            </div>
          )}
        </div>
        {activeRunId && (
          <a
            href={api.briefUrl(activeRunId)}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-accent/50 bg-accent/10 px-3.5 py-2 text-sm font-semibold text-accent transition hover:bg-accent/20"
          >
            ⭳ Export brief
          </a>
        )}
      </div>

      {recommendations.length === 0 ? (
        <div className="card flex h-64 items-center justify-center text-sm text-slate-500">
          Recommendations appear once a scenario runs (or the escalation demo auto-triggers one).
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {recommendations.map((rec) => (
            <RecommendationCard key={rec.id} rec={rec} />
          ))}
        </div>
      )}
    </div>
  );
}
