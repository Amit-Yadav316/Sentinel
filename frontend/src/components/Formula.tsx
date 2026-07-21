import { useState } from "react";

/** An ⓘ marker that reveals the formula string used to compute a number. */
export function Formula({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-block">
      <button
        onClick={() => setOpen((v) => !v)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 text-[10px] text-slate-500 hover:border-accent hover:text-accent"
        aria-label="how this was computed"
      >
        i
      </button>
      {open && (
        <span className="absolute bottom-6 left-1/2 z-20 w-72 -translate-x-1/2 rounded-lg border border-line bg-surface p-2.5 text-left text-[11px] font-normal leading-relaxed text-slate-600 shadow-lg">
          <span className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-accent">
            how computed
          </span>
          <span className="font-mono">{text}</span>
        </span>
      )}
    </span>
  );
}
