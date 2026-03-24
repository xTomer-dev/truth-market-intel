"use client";

import { useState } from "react";
import type { EvidenceItem } from "@/lib/api";
import { polarityColor } from "@/lib/intelligence";

type Props = {
  items: EvidenceItem[];
};

export default function EvidenceDrawer({ items }: Props) {
  const [open, setOpen] = useState(false);

  if (items.length === 0) {
    return <span className="text-xs text-[#4b5563]">No evidence</span>;
  }

  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-xs text-[#6b7280] transition hover:text-[#d1d5db]"
      >
        <span className="font-mono">{items.length} cite{items.length !== 1 ? "s" : ""}</span>
        <span
          className="transition-transform duration-200"
          style={{ display: "inline-block", transform: open ? "rotate(90deg)" : "rotate(0deg)" }}
        >
          ›
        </span>
      </button>

      <div
        className="overflow-hidden transition-all duration-200"
        style={{ maxHeight: open ? "600px" : "0px" }}
      >
        <div className="mt-2 space-y-2">
          {items.map((item) => (
            <div
              key={item.claim_id}
              className="rounded border border-[#1f2937] bg-[#0f172a] p-3"
            >
              {item.verbatim && (
                <blockquote className="mb-2 border-l-2 border-[#374151] pl-3 font-mono text-[11px] leading-relaxed text-[#9ca3af] italic">
                  &ldquo;{item.verbatim}&rdquo;
                </blockquote>
              )}
              {item.summary && (
                <p className="text-xs leading-relaxed text-[#d1d5db]">{item.summary}</p>
              )}
              <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-[#6b7280]">
                {item.speaker && <span>{item.speaker}</span>}
                {item.section && <span className="text-[#4b5563]">{item.section}</span>}
                {item.polarity && (
                  <span
                    className="rounded px-1 py-0.5 font-semibold uppercase tracking-wider"
                    style={{
                      color: polarityColor(item.polarity),
                      backgroundColor: `${polarityColor(item.polarity)}15`,
                    }}
                  >
                    {item.polarity}
                  </span>
                )}
                {item.confidence != null && (
                  <span className="font-mono">{(item.confidence * 100).toFixed(0)}% conf</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
