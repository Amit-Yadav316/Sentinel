import type { NewsItem } from "../lib/types";
import { riskColor } from "../lib/format";

function sevColor(sev: number): string {
  // reuse the risk ramp on a 0..1 severity by scaling to 0..100
  return riskColor(sev * 100 + 20);
}

export function SignalFeed({ items, source }: { items: NewsItem[]; source: string }) {
  const live = source === "live";
  return (
    <div className="card flex min-h-0 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-3 py-2">
        <span className="stat-label">Live signal feed · GDELT</span>
        {live ? (
          <span className="chip border border-emerald-200 bg-emerald-50 text-emerald-700">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 live-dot" /> live
          </span>
        ) : (
          <span className="chip border border-slate-200 bg-slate-100 text-slate-500">baseline</span>
        )}
      </div>
      <div className="max-h-56 flex-1 space-y-1.5 overflow-y-auto p-2.5">
        {items.length === 0 && <div className="p-2 text-[12px] text-slate-400">Loading news…</div>}
        {items.map((it, i) => (
          <div key={i} className="rounded-lg border border-line bg-slate-50/60 px-2.5 py-1.5">
            <div className="flex items-start gap-2">
              <span
                className="mt-1 h-2 w-2 shrink-0 rounded-full"
                style={{ background: sevColor(it.severity) }}
                title={`severity ${it.severity}`}
              />
              <div className="min-w-0">
                <div className="truncate text-[12.5px] leading-snug text-slate-700" title={it.headline}>
                  {it.headline}
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-1 text-[10px] text-slate-500">
                  <span className="rounded bg-slate-200/70 px-1.5 py-0.5 font-mono text-slate-600">
                    {it.event_type.replace(/_/g, " ")}
                  </span>
                  {it.corridor && (
                    <span className="rounded bg-sky-100 px-1.5 py-0.5 font-mono text-sky-700">
                      {it.corridor}
                    </span>
                  )}
                  {it.domain && <span className="truncate text-slate-400">{it.domain}</span>}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="border-t border-line px-3 py-1.5 text-[10px] text-slate-400">
        Real headlines classified live by the extraction agent · display-only (not scored)
      </div>
    </div>
  );
}
