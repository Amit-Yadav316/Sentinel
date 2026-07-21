import { create } from "zustand";
import { api, connectRiskStream } from "../lib/api";
import type {
  Corridor,
  CorridorRisk,
  Recommendation,
  ScenarioRun,
  ScenarioSummary,
  Vessel,
} from "../lib/types";

interface StoreState {
  corridors: Corridor[];
  risk: CorridorRisk[];
  vessels: Vessel[];
  vesselSource: "synthetic" | "live";
  brent: number;
  brentSeries: { date: string; value: number }[];
  brentSource: "cache" | "live";
  brentAsOf: string | null;
  scenarios: ScenarioSummary[];
  runs: ScenarioRun[];
  recommendations: Recommendation[];
  selectedCorridor: string | null;
  activeRunId: number | null;
  demoRunning: boolean;
  demoStep: number;
  demoTotal: number;
  lastEventHeadline: string | null;
  wsConnected: boolean;

  loadAll: () => Promise<void>;
  connect: () => void;
  selectCorridor: (id: string | null) => void;
  runScenario: (name: string) => Promise<void>;
  selectRun: (runId: number) => Promise<void>;
  startEscalation: () => Promise<void>;
  handleWs: (msg: any) => void;
}

let closeWs: (() => void) | null = null;

export const useStore = create<StoreState>((set, get) => ({
  corridors: [],
  risk: [],
  vessels: [],
  vesselSource: "synthetic",
  brent: 0,
  brentSeries: [],
  brentSource: "cache",
  brentAsOf: null,
  scenarios: [],
  runs: [],
  recommendations: [],
  selectedCorridor: null,
  activeRunId: null,
  demoRunning: false,
  demoStep: 0,
  demoTotal: 0,
  lastEventHeadline: null,
  wsConnected: false,

  loadAll: async () => {
    const [corridors, risk, vessels, brent, scenarios, runs] = await Promise.all([
      api.corridors(),
      api.risk(),
      api.vessels(),
      api.brent(),
      api.scenarios(),
      api.runs(),
    ]);
    set({
      corridors,
      risk,
      vessels,
      brent: brent.latest,
      brentSeries: brent.series,
      scenarios,
      runs,
    });
    if (runs.length > 0) {
      await get().selectRun(runs[0].id);
    }
    // Upgrade the cached price to a real-time quote in the background — never
    // blocks initial render, and silently keeps cache if offline.
    api
      .brentLive()
      .then((b) =>
        set({
          brent: b.latest,
          brentSeries: b.series,
          brentSource: b.source === "live" ? "live" : "cache",
          brentAsOf: b.as_of ?? null,
        }),
      )
      .catch(() => {});
    // Upgrade vessels to a real AISStream feed if a key is configured.
    api
      .vesselsLive()
      .then((r) => {
        if (r.source === "live") set({ vessels: r.vessels, vesselSource: "live" });
      })
      .catch(() => {});
  },

  connect: () => {
    if (closeWs) return;
    closeWs = connectRiskStream((msg) => get().handleWs(msg));
    set({ wsConnected: true });
  },

  selectCorridor: (id) => set({ selectedCorridor: id }),

  runScenario: async (name) => {
    const res = await api.runScenario(name);
    const runs = await api.runs();
    set({ runs, activeRunId: res.run_id, recommendations: res.recommendations });
  },

  selectRun: async (runId) => {
    const recs = await api.recommendations(runId);
    set({ activeRunId: runId, recommendations: recs });
  },

  startEscalation: async () => {
    set({ demoRunning: true, demoStep: 0 });
    await api.startEscalation(4);
  },

  handleWs: (msg) => {
    if (msg.type === "demo_start") {
      set({ demoRunning: true, demoStep: 0, demoTotal: msg.steps });
      return;
    }
    if (msg.type === "demo_end") {
      set({ demoRunning: false });
      // Refresh runs list after the demo completes.
      api.runs().then((runs) => set({ runs }));
      return;
    }
    if (msg.type === "event") {
      set((s) => ({
        risk: mergeRisk(s.risk, msg.risk),
        lastEventHeadline: msg.event?.headline ?? s.lastEventHeadline,
        demoStep: msg.step ?? s.demoStep,
      }));
      if (msg.scenario_run) {
        set({
          activeRunId: msg.scenario_run.id,
          recommendations: (msg.recommendations ?? []).map((r: any) => ({
            id: r.id,
            run_id: msg.scenario_run.id,
            rank: r.rank,
            payload: r.payload,
          })),
        });
        api.runs().then((runs) => set({ runs }));
      }
    }
  },
}));

/** Merge streamed {corridor, score, name} into the full risk objects. */
function mergeRisk(
  current: CorridorRisk[],
  updates: { corridor: string; score: number; name: string }[],
): CorridorRisk[] {
  const byId = new Map(current.map((r) => [r.corridor, r]));
  for (const u of updates) {
    const existing = byId.get(u.corridor);
    if (existing) {
      byId.set(u.corridor, { ...existing, score: u.score });
    }
  }
  // Refetch full evidence asynchronously so the evidence panel stays current.
  api.risk().then((full) => useStore.setState({ risk: full })).catch(() => {});
  return current.map((r) => byId.get(r.corridor) ?? r);
}
