export interface Corridor {
  id: string;
  name: string;
  chokepoint: { name: string; lat: number; lon: number };
  baseline_share: number;
  transit_days: number;
  origin: { lat: number; lon: number };
  destination: { lat: number; lon: number };
}

export interface RiskContribution {
  event_id: number | null;
  headline: string;
  event_type: string;
  weight: number;
  severity: number;
  age_hours: number;
  decay: number;
  contribution: number;
}

export interface CorridorRisk {
  corridor: string;
  name: string;
  score: number;
  baseline: number;
  weighted_sum: number;
  formula: string;
  computed_at: string;
  contributions: RiskContribution[];
}

export interface NewsItem {
  headline: string;
  url: string | null;
  domain: string | null;
  seendate: string | null;
  event_type: string;
  corridor: string | null;
  severity: number;
  confidence: number;
}

export interface Vessel {
  mmsi: string;
  name: string;
  lat: number;
  lon: number;
  corridor: string | null;
  synthetic: boolean;
}

export interface ScenarioSummary {
  name: string;
  title: string;
  description: string;
}

export interface RefineryShortfall {
  refinery_id: string;
  name: string;
  capacity_kbd: number;
  shortfall_kbd: number;
  shortfall_pct: number;
}

export interface ScenarioResult {
  scenario_name: string;
  net_imports_kbd: number;
  supply_gap_kbd: number;
  supply_gap_pct: number;
  refinery_shortfalls: RefineryShortfall[];
  spr_runway_days: number;
  landed_cost_delta_usd_bbl: number;
  brent_after_usd: number;
  retail_passthrough_inr_l: number;
  import_bill_delta_usd_bn: number;
  gdp_drag_pp: number;
  cad_widen_pp: number;
  power_stress_index: number;
  reserve_kb: number;
  formulas: Record<string, string>;
  assumptions_used: Record<string, number>;
}

export interface ScenarioRun {
  id: number;
  scenario_name: string;
  scenario_title: string;
  triggered_by: string;
  created_at: string;
  result: ScenarioResult;
}

export interface Recommendation {
  id: number;
  run_id: number;
  rank: number;
  payload: {
    crude: string;
    crude_id: string;
    source: string;
    route: string;
    load_port: string;
    volume_kbd: number;
    eta_days: number;
    cost_delta_usd_bbl: number;
    availability_index: number;
    compatible_refineries: string[];
    compatible_count: number;
    rank_score: number;
    rationale: string;
    caveats: string[];
  };
}
