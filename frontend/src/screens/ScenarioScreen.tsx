import { useStore } from "../store/store";
import { ScenarioResultView } from "../components/ScenarioResult";

export function ScenarioScreen() {
  const { scenarios, runs, activeRunId, selectRun, runScenario } = useStore();
  const activeRun = runs.find((r) => r.id === activeRunId) ?? runs[0];

  return (
    <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-4">
      <div className="space-y-4 lg:col-span-1">
        <div className="card p-4">
          <div className="mb-2 text-sm font-semibold text-slate-900">Run a scenario</div>
          <div className="space-y-2">
            {scenarios.map((s) => (
              <button
                key={s.name}
                onClick={() => runScenario(s.name)}
                className="w-full rounded-lg border border-line bg-slate-50 p-2.5 text-left transition hover:border-accent hover:bg-accent-soft"
              >
                <div className="text-[13px] font-semibold text-slate-900">{s.title}</div>
                <div className="mt-0.5 text-[11px] leading-snug text-slate-500">{s.description}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="card p-4">
          <div className="mb-2 text-sm font-semibold text-slate-900">Run history</div>
          <div className="space-y-1.5">
            {runs.length === 0 && <div className="text-[12px] text-slate-400">No runs yet.</div>}
            {runs.map((r) => (
              <button
                key={r.id}
                onClick={() => selectRun(r.id)}
                className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-[12px] transition ${
                  activeRun?.id === r.id ? "bg-accent-soft text-accent-600" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <span className="truncate">{r.scenario_title}</span>
                <span
                  className={`chip ${
                    r.triggered_by.startsWith("auto")
                      ? "bg-red-50 text-red-700 border border-red-200"
                      : "bg-slate-100 text-slate-500 border border-slate-200"
                  }`}
                >
                  {r.triggered_by.startsWith("auto") ? "auto" : "manual"}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="lg:col-span-3">
        {activeRun ? (
          <div className="space-y-4">
            <div className="card flex items-center justify-between p-4">
              <div>
                <div className="stat-label">Scenario result</div>
                <div className="text-lg font-semibold text-slate-900">{activeRun.scenario_title}</div>
              </div>
              {activeRun.triggered_by.startsWith("auto") && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-[12px] font-semibold text-red-700">
                  ⚡ Auto-triggered by {activeRun.triggered_by.split(":")[1]} risk breach
                </div>
              )}
            </div>
            <ScenarioResultView result={activeRun.result} />
          </div>
        ) : (
          <div className="card flex h-full items-center justify-center text-center text-sm text-slate-500">
            Run a scenario or trigger the escalation demo to see cascading impact.
          </div>
        )}
      </div>
    </div>
  );
}
