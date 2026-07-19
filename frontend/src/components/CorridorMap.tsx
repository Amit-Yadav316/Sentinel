import { useMemo } from "react";
import type { Corridor, CorridorRisk, Vessel } from "../lib/types";
import { riskColor } from "../lib/format";

// Equirectangular projection over a bounding box covering every corridor point
// (US Gulf .. Malacca, Cape .. Gulf). No basemap tiles => fully offline.
const W = 1000;
const H = 560;
const LON = [-102, 108];
const LAT = [-40, 46];

function project(lon: number, lat: number): [number, number] {
  const x = ((lon - LON[0]) / (LON[1] - LON[0])) * W;
  const y = ((LAT[1] - lat) / (LAT[1] - LAT[0])) * H;
  return [x, y];
}

function arcPath(o: { lat: number; lon: number }, d: { lat: number; lon: number }): string {
  const [x0, y0] = project(o.lon, o.lat);
  const [x1, y1] = project(d.lon, d.lat);
  const mx = (x0 + x1) / 2;
  const my = (y0 + y1) / 2;
  // Perpendicular bow so overlapping corridors separate visually.
  const dx = x1 - x0;
  const dy = y1 - y0;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;
  const bow = 0.18 * len;
  return `M ${x0} ${y0} Q ${mx + nx * bow} ${my + ny * bow} ${x1} ${y1}`;
}

export function CorridorMap({
  corridors,
  risk,
  vessels,
  selected,
  onSelect,
}: {
  corridors: Corridor[];
  risk: CorridorRisk[];
  vessels: Vessel[];
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  const riskById = useMemo(() => new Map(risk.map((r) => [r.corridor, r])), [risk]);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-full w-full">
      <defs>
        <radialGradient id="sea" cx="45%" cy="40%" r="80%">
          <stop offset="0%" stopColor="#0f1a2e" />
          <stop offset="100%" stopColor="#0a0e17" />
        </radialGradient>
      </defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#sea)" />

      {/* graticule */}
      {Array.from({ length: 8 }).map((_, i) => (
        <line key={`v${i}`} x1={(i * W) / 8} y1={0} x2={(i * W) / 8} y2={H} stroke="#1b2540" strokeWidth={0.5} />
      ))}
      {Array.from({ length: 5 }).map((_, i) => (
        <line key={`h${i}`} x1={0} y1={(i * H) / 5} x2={W} y2={(i * H) / 5} stroke="#1b2540" strokeWidth={0.5} />
      ))}

      {/* corridor arcs */}
      {corridors.map((c) => {
        const score = riskById.get(c.id)?.score ?? 30;
        const color = riskColor(score);
        const isSel = selected === c.id;
        const width = 1.5 + c.baseline_share * 12;
        return (
          <g key={c.id} className="cursor-pointer" onClick={() => onSelect(c.id)}>
            <path d={arcPath(c.origin, c.destination)} fill="none" stroke={color} strokeWidth={width}
              strokeOpacity={isSel ? 0.95 : 0.6} strokeLinecap="round" />
            <path d={arcPath(c.origin, c.destination)} fill="none" stroke={color} strokeWidth={width}
              strokeOpacity={0.9} strokeDasharray="2 14" strokeLinecap="round">
              <animate attributeName="stroke-dashoffset" from="0" to="-16" dur="1.1s" repeatCount="indefinite" />
            </path>
            {isSel && (
              <path d={arcPath(c.origin, c.destination)} fill="none" stroke={color} strokeWidth={width + 6}
                strokeOpacity={0.15} strokeLinecap="round" />
            )}
          </g>
        );
      })}

      {/* vessels */}
      {vessels.map((v) => {
        const [x, y] = project(v.lon, v.lat);
        const score = v.corridor ? riskById.get(v.corridor)?.score ?? 30 : 30;
        return <circle key={v.mmsi} cx={x} cy={y} r={1.8} fill={riskColor(score)} fillOpacity={0.85} />;
      })}

      {/* chokepoints */}
      {corridors.map((c) => {
        const [x, y] = project(c.chokepoint.lon, c.chokepoint.lat);
        const score = riskById.get(c.id)?.score ?? 30;
        return (
          <g key={`cp-${c.id}`} onClick={() => onSelect(c.id)} className="cursor-pointer">
            <rect x={x - 3.5} y={y - 3.5} width={7} height={7} transform={`rotate(45 ${x} ${y})`}
              fill="#0a0e17" stroke={riskColor(score)} strokeWidth={1.5} />
            <text x={x + 8} y={y + 3} fill="#94a3b8" fontSize={10} className="font-mono">
              {c.chokepoint.name}
            </text>
          </g>
        );
      })}

      {/* India marker */}
      {(() => {
        const [x, y] = project(78, 22);
        return (
          <g>
            <circle cx={x} cy={y} r={3} fill="#38bdf8" />
            <text x={x + 6} y={y - 4} fill="#e2e8f0" fontSize={12} fontWeight={600}>
              INDIA
            </text>
            <text x={x + 6} y={y + 8} fill="#64748b" fontSize={9} className="font-mono">
              west-coast refineries
            </text>
          </g>
        );
      })()}
    </svg>
  );
}
