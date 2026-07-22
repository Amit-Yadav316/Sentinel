import type { NewsItem } from "../lib/types";
import { riskColor } from "../lib/format";

function sevColor(sev: number): string {
  return riskColor(sev * 100 + 20);
}

export function SignalFeed({ items, source }: { items: NewsItem[]; source: string }) {
  const live = source === "live";
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <span className="text-base font-semibold text-slate-800">Live Signal Feed</span>
        {live ? (
          <span className="chip border border-emerald-200 bg-emerald-50 text-emerald-700">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 live-dot" /> live · GDELT
          </span>
        ) : (
          <span className="chip border border-slate-200 bg-slate-100 text-slate-500">baseline</span>
        )}
      </div>
      <div className="max-h-64 space-y-2 overflow-y-auto p-3">
        {items.length === 0 && <div className="p-2 text-sm text-slate-400">Loading the latest headlines…</div>}
        {items.map((it, i) => (
          <div key={i} className="rounded-lg border border-line bg-slate-50/70 px-3 py-2.5">
            <div className="flex items-start gap-2.5">
              <span
                className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ background: sevColor(it.severity) }}
                title={`severity ${it.severity}`}
              />
              <div className="min-w-0">
                <div className="text-sm leading-snug text-slate-700">{it.headline}</div>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
                  <span className="rounded bg-slate-200/70 px-2 py-0.5 text-slate-600">
                    {it.event_type.replace(/_/g, " ")}
                  </span>
                  {it.corridor && (
                    <span className="rounded bg-sky-100 px-2 py-0.5 text-sky-700">{it.corridor}</span>
                  )}
                  {it.domain && <span className="truncate text-slate-400">{it.domain}</span>}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="border-t border-line px-4 py-2.5 text-xs text-slate-400">
        Live headlines classified by the extraction agent · display-only (not scored).
      </div>
    </div>
  );
}
