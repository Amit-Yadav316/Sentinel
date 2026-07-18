import type {
  Corridor,
  CorridorRisk,
  Recommendation,
  ScenarioRun,
  ScenarioSummary,
  Vessel,
} from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "POST" });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export const api = {
  corridors: () => get<Corridor[]>("/corridors"),
  risk: () => get<CorridorRisk[]>("/corridors/risk"),
  vessels: () => get<Vessel[]>("/vessels"),
  brent: () => get<{ latest: number; series: { date: string; value: number }[] }>("/prices/brent"),
  scenarios: () => get<ScenarioSummary[]>("/scenarios"),
  runScenario: (name: string) =>
    post<{ run_id: number; result: ScenarioRun["result"]; recommendations: Recommendation[] }>(
      `/scenarios/${name}/run`,
    ),
  runs: () => get<ScenarioRun[]>("/scenario-runs"),
  recommendations: (runId?: number) =>
    get<Recommendation[]>(`/recommendations${runId ? `?run_id=${runId}` : ""}`),
  startEscalation: (stepDelay = 4) =>
    post<{ status: string; steps: number }>(`/demo/escalate?step_delay=${stepDelay}`),
  briefUrl: (runId: number) => `${BASE}/runs/${runId}/brief`,
};

/** Connect to the risk websocket. Returns a close fn. */
export function connectRiskStream(onMessage: (msg: any) => void): () => void {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/risk/stream`);
  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data));
    } catch {
      /* ignore malformed frames */
    }
  };
  // Keep-alive ping so the server receive loop stays happy.
  const ping = setInterval(() => ws.readyState === ws.OPEN && ws.send("ping"), 15000);
  return () => {
    clearInterval(ping);
    ws.close();
  };
}
