import { useMemo } from "react";
import type { Corridor, CorridorRisk, Vessel } from "../lib/types";
import { riskColor } from "../lib/format";
import landRaw from "../lib/land.json";

// Real public-domain coastline geography (Natural Earth 110m):
// feature -> polygon -> ring -> [lon, lat]  (5 array levels).
const LAND = landRaw as unknown as number[][][][][];

// Equirectangular projection over a bounding box covering every corridor point
// (US Gulf .. Malacca, Cape .. Gulf). No basemap tiles => fully offline.
const W = 1000;
const H = 560;
// Focused on the Indian Ocean theatre (Red Sea → Malacca) where the demo lives;
// long-haul Cape/Atlantic corridors enter from the map edge.
const LON = [30, 103];
const LAT = [-8, 40];

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
  const dx = x1 - x0;
  const dy = y1 - y0;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;
  const bow = Math.min(0.18 * len, 90); // cap so off-map long-haul arcs stay sane
  return `M ${x0} ${y0} Q ${mx + nx * bow} ${my + ny * bow} ${x1} ${y1}`;
}

function polyPath(polygon: number[][][]): string {
  return polygon
    .map(
      (ring) =>
        "M " +
        ring
          .map(([lon, lat]) => {
            const [x, y] = project(lon, lat);
            return `${x.toFixed(1)} ${y.toFixed(1)}`;
          })
          .join(" L ") +
        " Z",
    )
    .join(" ");
}

// Precompute land paths once (module-level; geography never changes).
const LAND_PATHS = LAND.flat().map(polyPath);

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
        <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#eaf1fb" />
          <stop offset="100%" stopColor="#dfeaf6" />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#sea)" />

      {/* real coastline basemap (Natural Earth) */}
      <g>
        {LAND_PATHS.map((d, i) => (
          <path key={i} d={d} fill="#e7ebe1" stroke="#cdd4c6" strokeWidth={0.4} fillRule="evenodd" />
        ))}
      </g>

      {/* graticule */}
      {Array.from({ length: 8 }).map((_, i) => (
        <line key={`v${i}`} x1={(i * W) / 8} y1={0} x2={(i * W) / 8} y2={H} stroke="#cdddf0" strokeWidth={0.5} />
      ))}
      {Array.from({ length: 5 }).map((_, i) => (
        <line key={`h${i}`} x1={0} y1={(i * H) / 5} x2={W} y2={(i * H) / 5} stroke="#cdddf0" strokeWidth={0.5} />
      ))}

      {/* corridor arcs */}
      {corridors.map((c) => {
        const score = riskById.get(c.id)?.score ?? 30;
        const color = riskColor(score);
        const isSel = selected === c.id;
        const width = 1.5 + c.baseline_share * 12;
        return (
          <g key={c.id} className="cursor-pointer" onClick={() => onSelect(c.id)}>
            {isSel && (
              <path d={arcPath(c.origin, c.destination)} fill="none" stroke={color} strokeWidth={width + 8}
                strokeOpacity={0.18} strokeLinecap="round" />
            )}
            <path d={arcPath(c.origin, c.destination)} fill="none" stroke={color} strokeWidth={width}
              strokeOpacity={isSel ? 1 : 0.8} strokeLinecap="round" />
            <path d={arcPath(c.origin, c.destination)} fill="none" stroke="#ffffff" strokeWidth={width}
              strokeOpacity={0.75} strokeDasharray="2 14" strokeLinecap="round">
              <animate attributeName="stroke-dashoffset" from="0" to="-16" dur="1.1s" repeatCount="indefinite" />
            </path>
          </g>
        );
      })}

      {/* vessels (corridor-tinted for synthetic; neutral for live AIS) */}
      {vessels.map((v) => {
        const [x, y] = project(v.lon, v.lat);
        const fill = v.corridor ? riskColor(riskById.get(v.corridor)?.score ?? 30) : "#334e68";
        return (
          <circle key={v.mmsi} cx={x} cy={y} r={2} fill={fill} fillOpacity={0.95}
            stroke="#ffffff" strokeWidth={0.6} />
        );
      })}

      {/* chokepoints */}
      {corridors.map((c) => {
        const [x, y] = project(c.chokepoint.lon, c.chokepoint.lat);
        const score = riskById.get(c.id)?.score ?? 30;
        return (
          <g key={`cp-${c.id}`} onClick={() => onSelect(c.id)} className="cursor-pointer">
            <rect x={x - 3.5} y={y - 3.5} width={7} height={7} transform={`rotate(45 ${x} ${y})`}
              fill="#ffffff" stroke={riskColor(score)} strokeWidth={1.8} />
            <text x={x + 8} y={y + 3} fill="#475569" fontSize={10} className="font-mono">
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
            <circle cx={x} cy={y} r={3.5} fill="#2a78d6" stroke="#ffffff" strokeWidth={1} />
            <text x={x + 7} y={y - 4} fill="#0f172a" fontSize={12} fontWeight={700}>
              INDIA
            </text>
            <text x={x + 7} y={y + 8} fill="#64748b" fontSize={9} className="font-mono">
              west-coast refineries
            </text>
          </g>
        );
      })()}
    </svg>
  );
}
